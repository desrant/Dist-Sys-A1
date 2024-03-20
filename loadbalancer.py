from flask import Flask, request, jsonify, Response
import docker
import os
import re
import requests
import json
app = Flask(__name__)
import mysql.connector
# Setup Docker client
client = docker.from_env()
server_image_name = os.getenv('SERVER_IMAGE_NAME', 'dist-sys-a1-test-server')

# Docker Operations
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
                environment=[
                    "SERVER_ID=" + server_name,
                    "MYSQL_HOST=dist-sys-a1-test-db-1",
                    "MYSQL_ROOT_PASSWORD=rootpassword"
                ],
                mem_limit='200m',
                cpu_quota=int(0.2 * 100000),  # Equivalent to 20% of CPU
                network='d1_my_network'
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

# Consistent Hashing With Probing
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

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'dist-sys-a1-test-db-1')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_ROOT_PASSWORD')

def db_connect():
    # Connect to MySQL without specifying a database
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cursor = connection.cursor()

    # Check if the 'datashards' database exists
    cursor.execute("SHOW DATABASES LIKE 'datashards'")
    result = cursor.fetchone()

    # If the 'datashards' database does not exist, create it
    if not result:
        cursor.execute("CREATE DATABASE datashards")
        print("Database 'datashards' created successfully.")

    cursor.close()
    connection.close()

    # Reconnect to MySQL, this time to the 'datashards' database specifically
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database='datashards'
    )
    return connection

def initialize_shardT_and_mapT():
    db = db_connect()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ShardT (
            Stud_id_low INT PRIMARY KEY,
            Shard_id VARCHAR(255),
            Shard_size INT,
            valid_idx INT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MapT (
            Shard_id VARCHAR(255),
            Server_id VARCHAR(255),
            PRIMARY KEY (Shard_id, Server_id)
        )
    """)
    db.commit()
    cursor.close()
    db.close()

@app.route('/init', methods=['POST'])
def handle_init():
    data = request.json
    db = db_connect()
    cursor = db.cursor()
    initialize_shardT_and_mapT()
    print(json.dumps(data, indent=4))
    # Initialize ShardT and MapT tables with the received configuration
    for shard in data.get('shards', []):
        cursor.execute("INSERT INTO ShardT (Stud_id_low, Shard_id, Shard_size, valid_idx) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE Shard_size = VALUES(Shard_size)",
                       (shard['Stud_id_low'], shard['Shard_id'], shard['Shard_size'], 0))

    for server_id, shard_ids in data.get('servers', {}).items():
        for shard_id in shard_ids:
            cursor.execute("INSERT INTO MapT (Shard_id, Server_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE Server_id = VALUES(Server_id)",
                           (shard_id, server_id))
    for server_name, shards in data.get('servers', {}).items():
        # Create a new JSON object with the server name as the key and the shards list as the value
        new_json = {"schema": data.get('schema',{}),
                    "shards": shards
                    }
    
        match = re.search(r"Server(\d+)", server_name)
        port = int(match.group(1)) + 8000 if match else 8000
        url = f'http://host.docker.internal:{port}/config'
        response = requests.post(url, json=new_json)  # Set timeout to 30 seconds


        # Check response status and act accordingly
        if response.status_code == 200:
            print(f"Successfully sent data for {server_name}")
        else:
            print(f"Failed to send data for {server_name}: {response.status_code}")

        
        
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({"message": "Configured Database", "status": "success"}), 200



@app.route('/heartbeat', methods=['GET'])
def handle_get_request():
    consistent_hashing.request_id+=1
    server_name = consistent_hashing.get_server(consistent_hashing.request_id)
    match = re.search(r"Server(\d+)_VN\d+", server_name)
    port = int(match.group(1)) + 8000 if match else 8000
    target_url = f'http://host.docker.internal:{port}{request.path}'

    try:
        # Forward the request to the target server
        consistent_hashing.add_servers()
        response = requests.get(target_url)
        
        # Create a Flask response object from the forwarded request's response
        forwarded_response = Response(response.content, status=response.status_code, content_type=response.headers['Content-Type'])
        return forwarded_response
    except requests.exceptions.RequestException as e:
        # Return a 502 Bad Gateway error if the request to the target server fails
        return jsonify({"error": str(e)}), 502
    


# Flask route for reporting server replicas
@app.route('/rep', methods=['GET'])
def report_replicas():
    servers_with_vn = [server for server in consistent_hashing.hash_map if server is not None]
    unique_servers = set()  # Use a set to store unique server names
    for server in servers_with_vn:
        base_server_name = server.split("_VN")[0]  # Split by "_VN" and take the first part
        unique_servers.add(base_server_name)
    
    response = {
        "message": {
            "N": len(unique_servers),
            "replicas": list(unique_servers)
        },
        "status": "successful"
    }
    return jsonify(response), 200

# Flask route for adding servers
@app.route('/add', methods=['POST'])
def add_servers():
    data = request.get_json()

    # Check if 'n' and 'hostnames' are in the JSON data and if the length of 'hostnames' matches 'n'
    if data and 'n' in data and 'hostnames' in data and len(data['hostnames']) == data['n']:
        for hostname in data['hostnames']:
            consistent_hashing.add_new_server(hostname)
            match = re.search(r"Server(\d+)", hostname)

            port = int(match.group(1)) + 8000 if match else 8000
            up_server_container(hostname, port)

        # Use jsonify to return a JSON response
        return jsonify({"message": "Servers added successfully", "status": "successful"}), 200
    else:
        return jsonify({"message": "Incorrect number of hostnames or missing 'n'", "status": "failure"}), 400

# Flask route for removing servers
@app.route('/rm', methods=['DELETE'])
def remove_servers():
    data = request.get_json()

    # Validate the JSON data for 'n' and 'hostnames', and check if lengths match
    if data and 'n' in data and 'hostnames' in data and len(data['hostnames']) == data['n']:
        for hostname in data['hostnames']:
            down_server_container(hostname)
            consistent_hashing.remove_server(hostname)

        # Return a JSON response indicating success
        return jsonify({"message": "Servers removed successfully", "status": "successful"}), 200
    else:
        # Return a JSON response indicating failure due to incorrect data
        return jsonify({"message": "Incorrect number of hostnames or missing 'n'", "status": "failure"}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
