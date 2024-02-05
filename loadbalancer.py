import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import re
from urllib.parse import urlparse, parse_qs

class ConsistentHashingWithProbing:
    def __init__(self, num_slots=512, num_servers=3, virtual_nodes_per_server=9):
        self.num_slots = num_slots
        self.hash_map = [None] * num_slots
        self.num_servers = num_servers
        self.virtual_nodes_per_server = virtual_nodes_per_server
        self.add_servers()

    def hash_request(self, i):
        return (i ** 2 + 2 * i + 17) % self.num_slots

    def hash_server(self, i, j):
        return (i ** 2 + j ** 2 + 2 * j + 25) % self.num_slots

    def add_servers(self):
        for i in range(self.num_servers):
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
        # slot=hash(server_name)%self.num_slots
        while self.hash_map[slot] is not None:
            slot = (slot + 1) % self.num_slots
        self.hash_map[slot] = server_name

    def remove_server(self, server_name):
        slot = hash(server_name) % self.num_slots
        while self.hash_map[slot] != server_name:
            slot = (slot + 1) % self.num_slots
        self.hash_map[slot] = None

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
        
        if self.path == '/get':
            servers = [server for server in consistent_hashing.hash_map if server is not None]
            self._send_response({"message": {"replicas": servers}, "status": "successful"})
        elif 'query' in query_params:
            request_id = int(query_params['query'][0])
            server_name = consistent_hashing.get_server(request_id)
            if server_name:
                self._send_response({"message": f"Request routed to server: {server_name}"})
            else:
                self._send_response({"message": "Service unavailable"}, 503)
        else:
            self._send_response({"message": "Invalid request format"}, 400)

    def do_POST(self):
        if self.path == '/add':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            if 'n' in post_data and 'hostnames' in post_data and len(post_data['hostnames']) == post_data['n']:
                for hostname in post_data['hostnames']:
                    consistent_hashing.add_new_server(hostname)
                self._send_response({"message": "Servers added successfully", "status": "successful"})
            else:
                self._send_response({"message": "Incorrect number of hostnames or missing 'n'", "status": "failure"}, 400)

    def do_DELETE(self):
        if self.path == '/rm':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            if 'n' in post_data and 'hostnames' in post_data and len(post_data['hostnames']) == post_data['n']:
                for hostname in post_data['hostnames']:
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
