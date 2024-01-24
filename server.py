import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleServer(BaseHTTPRequestHandler):
    server_id = os.getenv('SERVER_ID', 'default_server_id')  # Set a default value in case the environment variable is not set

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
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'')  # Send an empty byte string to ensure HTTP response format is correct


def run(server_class=HTTPServer, handler_class=SimpleServer, port=5000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
