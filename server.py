import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleServer(BaseHTTPRequestHandler):
    server_id = os.getenv('SERVER_ID', 'server_0')  # Set a default value in case the environment variable is not set

    def do_GET(self):
        if self.path == '/home':
            response = {
                "message": f"Hello from Server: {self.server_id}",
                "status": "successful"
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())  # Use json.dumps to convert the dictionary to a JSON formatted string
        elif self.path == '/heartbeat':
            response = {
                "message": f"Hello from Server: {self.server_id}",
                "status": "successful"
            }
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())  # Send an empty byte string to ensure HTTP response format is correct
from flask import Flask, jsonify
import os

app = Flask(__name__)
server_id = os.getenv('SERVER_ID', 'server_0')  # Set a default value in case the environment variable is not set

@app.route('/home', methods=['GET'])
def home():
    response = {
        "message": f"Hello from Server: {server_id}",
        "status": "successful"
    }
    return jsonify(response), 200

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    response = {
        "message": f"Hello from Server: {server_id}",
        "status": "successful"
    }
    return jsonify(response), 200

if __name__ == '__main__':
    # Define the port on which you want to run the server. Default is 5000.
    port = int(os.getenv('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
