import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import re
from urllib.parse import urlparse, parse_qs
import random
import requests
import docker
import os

client = docker.from_env()
server_image_name = os.getenv('SERVER_IMAGE_NAME', 'dist-sys-a1-test-server')

def up_server_container(server_name,host_port):
    container_name = server_name
    
    try:
        container = client.containers.get(container_name)
        if container.status == 'exited':
            print(f"Existing container {container_name} logs before restart:")
            print(container.logs().decode('utf-8'))  
            container.start()
            print(f"Container {container_name} started.")
    except docker.errors.NotFound:
        
        try:
            
            container = client.containers.run(
                server_image_name,
                name=container_name,
                detach=True,
                ports={str(8000): str(host_port)},
                environment=["SERVER_ID=" + server_name],
                network='my_network'
                )

            container.start()
            print(f"Container {container_name} created and started.")
        except docker.errors.ContainerError as e:
            print(f"Container {container_name} failed to start. Error: {e}")
        except docker.errors.ImageNotFound:
            print(f"Image {server_image_name} not found.")
        except docker.errors.APIError as e:
            print(f"Server error: {e}")

        import time
        time.sleep(2)  
        container = client.containers.get(container_name)
        if container.status == 'exited':
            print(f"Container {container_name} exited after creation. Logs:")
            print(container.logs().decode('utf-8'))  

def down_server_container(server_name):
    
    container_name = server_name
    try:
        container = client.containers.get(container_name)
        if container.status in ['running', 'paused']:
            print(f"Stopping container {container_name}...")
            container.stop()
            print(f"Container {container_name} stopped.")
        print(f"Removing container {container_name}...")
        container.remove()  # Remove the container after stopping it
        print(f"Container {container_name} removed.")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found, nothing to stop or remove.")
    except docker.errors.ContainerError as e:
        print(f"Error stopping container {container_name}: {e}")
    except Exception as e:
        print(f"General error with container {container_name}: {e}")






class ConsistentHashingWithProbing:
    def __init__(self, num_slots=512, num_servers=3, virtual_nodes_per_server=9, request_id=0):
        self.num_slots = num_slots
        self.hash_map = [None] * num_slots
        self.num_servers = num_servers
        self.virtual_nodes_per_server = virtual_nodes_per_server
        self.add_servers()
        self.request_id=request_id

    def hash_request(self, i):
        return (i ** 2 + 2 * i + 17) % self.num_slots

    def hash_server(self, i, j):
        return (i ** 2 + j ** 2 + 2 * j + 25) % self.num_slots

    def add_servers(self):
        for i in range(self.num_servers):
            up_server_container(f"Server{i}",8000+int(i))
            for j in range(self.virtual_nodes_per_server):
                self.add_server(f"Server{i}_VN{j}")

    def add_new_server(self,server_name):
        for i in range(self.virtual_nodes_per_server):
            self.add_server(server_name+f"_VN{i}")

    def add_server(self, server_name):
        matches = re.findall(r'\d+', server_name)
        i = int(matches[-2]) if matches else None
        j = int(matches[-1]) if len(matches) > 1 else None
        slot = self.hash_server(i,j)
        
        slot = self.hash_server(i, j)
        initial_slot = slot
        while True:
            if self.hash_map[slot] is None:  
                self.hash_map[slot] = server_name
                return True  
            elif self.hash_map[slot] == server_name:  
                return False  
            else:
                slot = (slot + 1) % self.num_slots
                if slot == initial_slot:  
                    break
        return False  

    def remove_server(self, server_name):
        servers_to_remove = [server_name + f"_VN{i}" for i in range(self.virtual_nodes_per_server)]
        for i in range(self.num_slots):
            if self.hash_map[i] in servers_to_remove:
                self.hash_map[i] = None
        self.ensure_minimum_servers()

    def ensure_minimum_servers(self):
        while len(set(self.get_server_names())) < 3:
            new_server_id = self.find_next_available_server_id()
            new_server_name = f"Server{new_server_id}"
            host_port=5000+int(new_server_id)
            up_server_container(new_server_name,host_port)
            self.add_new_server(new_server_name)
            
    def find_next_available_server_id(self):
        existing_ids = {int(server.split('Server')[1].split('_')[0]) for server in self.hash_map if server is not None}
        next_id = 0
        while next_id in existing_ids:
            next_id += 1
        return next_id

    def get_server_names(self):
        # Extract and return the unique base server names from the hash_map
        return [server.split("_VN")[0] for server in self.hash_map if server is not None]
    
    def get_server(self, request_id):
        slot = self.hash_request(request_id)
        while self.hash_map[slot] is None and slot < self.num_slots:
            slot = (slot + 1) % self.num_slots
        if slot == self.num_slots:
            return None
        return self.hash_map[slot]

    def clear_and_add_servers(self, num_servers, virtual_nodes_per_server=9):
        self.num_servers = num_servers
        self.virtual_nodes_per_server = virtual_nodes_per_server
        self.hash_map = [None] * self.num_slots
        self.add_servers()

consistent_hashing = ConsistentHashingWithProbing()

class LoadBalancerHandler(BaseHTTPRequestHandler):
    def _send_response(self, response, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Assuming /home and /heartbeat are paths that should be redirected
        if self.path in ['/home', '/heartbeat']:
            
            consistent_hashing.request_id+=1
            server = consistent_hashing.get_server(consistent_hashing.request_id)
            # Construct the target server URL based on the server name
            # This example assumes you have a way to resolve server_name to an actual URL or IP address
            # You might need a service registry or a static mapping to achieve this
            match = re.search(r"Server(\d+)_VN\d+", server) 

            port = int(match.group(1))+8000 if match else 8000

            target_url = f'http://host.docker.internal:{port}{self.path}'
            
            try:
                # Forward the request to the target server
                consistent_hashing.add_servers()
                response = requests.get(target_url)
                
                # Send the response back to the client
                self.send_response(response.status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(response.content)
            except requests.exceptions.RequestException as e:
                self.send_error(502, message=str(e))
            return

        if self.path == '/rep':
            # Extract server names without virtual nodes
            servers_with_vn = [server for server in consistent_hashing.hash_map if server is not None]
            unique_servers = set()  # Use a set to store unique server names
            for server in servers_with_vn:
                base_server_name = server.split("_VN")[0]  # Split by "_VN" and take the first part
                unique_servers.add(base_server_name)
            self._send_response({"message": {"N": len(unique_servers),"replicas": list(unique_servers)}, "status": "successful"})

    def do_POST(self):
        if self.path == '/add':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            if 'n' in post_data and 'hostnames' in post_data and len(post_data['hostnames']) == post_data['n']:
                for hostname in post_data['hostnames']:
                    consistent_hashing.add_new_server(hostname)
                    match = re.search(r"Server(\d+)", hostname) 

                    port = int(match.group(1))+8000 if match else 8000
                    up_server_container(hostname,port)
                self._send_response({"message": "Servers added successfully", "status": "successful"})
            else:
                self._send_response({"message": "Incorrect number of hostnames or missing 'n'", "status": "failure"}, 400)

    def do_DELETE(self):
        if self.path == '/rm':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            if 'n' in post_data and 'hostnames' in post_data and len(post_data['hostnames']) == post_data['n']:
                for hostname in post_data['hostnames']:
                    down_server_container(hostname)
                    consistent_hashing.remove_server(hostname)
                self._send_response({"message": "Servers removed successfully", "status": "successful"})
            else:
                self._send_response({"message": "Incorrect number of hostnames or missing 'n'", "status": "failure"}, 400)

def run(server_class=HTTPServer, handler_class=LoadBalancerHandler, port=5000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting load balancer on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
