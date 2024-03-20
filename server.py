from flask import Flask, request, jsonify
import os
import json
import mysql.connector

app = Flask(__name__)

# def get_shard_id_for_stud(stud_id):
#     db = mysql.connector.connect(
#         host=os.environ.get('MYSQL_HOST', 'localhost'), 
#         user=os.environ.get('MYSQL_USER', 'root'), 
#         password=os.environ.get('MYSQL_PASSWORD', 'yourpassword'), 
#         database=os.environ.get('MYSQL_DB', 'datashards')
#     )
#     cursor = db.cursor(dictionary=True)
    
#     query = """
#     SELECT Shard_id
#     FROM shard_metadata
#     WHERE %s >= Stud_id_low AND %s < Stud_id_low + Shard_size
#     LIMIT 1
#     """
#     cursor.execute(query, (stud_id, stud_id))
#     result = cursor.fetchone()
#     cursor.close()
#     db.close()
    
#     if result:
#         return result['Shard_id']
#     else:
#         return None


# Environment variables to determine server ID and assigned shards
SERVER_ID = os.environ.get('SERVER_ID', 'Server0')

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

# Function to create or update a shard schema
def create_or_update_shard_schema(shard_id, schema):
    db = db_connect()
    cursor = db.cursor()
    table_name = f"StudT_{shard_id}"
    
    # Check if table exists
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    result = cursor.fetchone()
    if result:
        return jsonify(message="Shard table already exist", status="success"), 200
    else:
        # Table doesn't exist, create new
        columns = schema['columns']
        dtypes = schema['dtypes']
        # Assuming 'Number' maps to 'INT' and 'String' maps to 'VARCHAR(255)'
        # Adjust the mapping as per your requirements
        type_mapping = {"Number": "INT", "String": "VARCHAR(255)"}
        columns_definition = ', '.join([f"{col} {type_mapping[dtype]}" for col, dtype in zip(columns, dtypes)])

        cursor.execute(f"CREATE TABLE {table_name} ({columns_definition}, PRIMARY KEY (Stud_id))")
    
    db.commit()
    cursor.close()
    db.close()

shards={}
@app.route('/config', methods=['POST'])
def configure_shards():
    global data
    data = request.json
    shards = data.get('shards', [])
    schema = data.get('schema', {})
    for shard_id in shards:
        create_or_update_shard_schema(shard_id, schema)
    
    response_message = f"{SERVER_ID} configured with shards: {', '.join(shards)}"
    return jsonify(message=response_message, status="success"), 200

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return jsonify({"server": SERVER_ID, "status": "alive"}), 200

# @app.route('/write', methods=['POST'])
# def write_data():
#     if not request.json or 'Stud_id' not in request.json:
#         return jsonify({"error": "Invalid request"}), 400
    
#     stud_id = request.json['Stud_id']
#     shard_id = request.json('shard_id')
#     entry = request.json

#     # Check if the shard is assigned to this server and if the shard is valid
#     if shard_id in shards:
#         try:
#             db = mysql.connector.connect(
#                 host=os.environ.get('MYSQL_HOST', 'localhost'), 
#                 user=os.environ.get('MYSQL_USER', 'root'), 
#                 password=os.environ.get('MYSQL_PASSWORD', 'yourpassword'), 
#                 database=os.environ.get('MYSQL_DB', 'datashards')
#             )
#             cursor = db.cursor(dictionary=True)
#             add_student = ("INSERT INTO StudT "
#                            "(Stud_id, Stud_name, Stud_marks, Shard_id) "
#                            "VALUES (%s, %s, %s, %s)")
#             data_student = (entry['Stud_id'], entry['Stud_name'], entry['Stud_marks'], shard_id)
#             cursor.execute(add_student, data_student)
#             db.commit()
#             cursor.close()
#             db.close()
#             return jsonify({"message": f"Data added to shard {shard_id} in {SERVER_ID}", "status": "success"}), 200
#         except mysql.connector.Error as err:
#             return jsonify({"error": str(err)}), 500
#     else:
#         return jsonify({"error": f"{SERVER_ID} does not handle shard {shard_id}"}), 400

# @app.route('/read', methods=['POST'])
# def read_data():
#     if not request.json or 'shard' not in request.json:
#         return jsonify({"error": "Invalid request"}), 400
    
#     shard = request.json['shard']

#     if shard in shards:
#         # Return all entries in the shard - in a real scenario, you'd filter or paginate this
#         return jsonify({shard: shards[shard], "status": "success"}), 200
#     else:
#         return jsonify({"error": f"{SERVER_ID} does not handle shard {shard}"}), 400

# @app.route('/delete', methods=['DELETE'])
# def delete_data():
#     if not request.json or 'Stud_id' not in request.json:
#         return jsonify({"error": "Invalid request"}), 400
    
#     stud_id = request.json['Stud_id']
#     shard_id = request.json['shard']

#     if shard_id in shards:
#         # Delete logic goes here
#         return jsonify({"message": f"Data entry with Stud_id: {stud_id} removed from shard {shard_id}", "status": "success"}), 200
#     else:
#         return jsonify({"error": f"{SERVER_ID} does not handle shard {shard_id}"}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)



































# import os
# import json
# from http.server import BaseHTTPRequestHandler, HTTPServer

# class SimpleServer(BaseHTTPRequestHandler):
#     server_id = os.getenv('SERVER_ID', 'server_0')  # Set a default value in case the environment variable is not set

#     def do_GET(self):
#         if self.path == '/home':
#             response = {
#                 "message": f"Hello from Server: {self.server_id}",
#                 "status": "successful"
#             }
#             self.send_response(200)
#             self.send_header('Content-type', 'application/json')
#             self.end_headers()
#             self.wfile.write(json.dumps(response).encode())  # Use json.dumps to convert the dictionary to a JSON formatted string
#         elif self.path == '/heartbeat':
#             response = {
#                 "message": f"Hello from Server: {self.server_id}",
#                 "status": "successful"
#             }
#             self.send_response(200)
#             self.end_headers()
#             self.wfile.write(json.dumps(response).encode())  # Send an empty byte string to ensure HTTP response format is correct
# from flask import Flask, jsonify
# import os

# app = Flask(__name__)
# server_id = os.getenv('SERVER_ID', 'server_0')  # Set a default value in case the environment variable is not set

# @app.route('/home', methods=['GET'])
# def home():
#     response = {
#         "message": f"Hello from Server: {server_id}",
#         "status": "successful"
#     }
#     return jsonify(response), 200

# @app.route('/heartbeat', methods=['GET'])
# def heartbeat():
#     response = {
#         "message": f"Hello from Server: {server_id}",
#         "status": "successful"
#     }
#     return jsonify(response), 200

# if __name__ == '__main__':
#     # Define the port on which you want to run the server. Default is 5000.
#     port = int(os.getenv('PORT', 8000))
#     app.run(debug=True, host='0.0.0.0', port=port)
