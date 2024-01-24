# Distributed Systems Assignment 1

This assignment demonstrates a simple distributed systems load balancer that routes incoming HTTP requests to multiple servers using consistent hashing with linear probing. The project consists of two main components: a Load Balancer and multiple Servers.

## Components

### Load Balancer

- The Load Balancer is responsible for distributing incoming client requests to the appropriate Server.
- It uses consistent hashing with linear probing to map client requests to Servers.
- Provides endpoints for adding, removing, and retrieving information about active Servers dynamically.
- Written in Python using the `http.server` module for handling HTTP requests.

### Servers

- Servers are the backend components that process client requests.
- Each Server is identified by a unique name (e.g., Server0_VN0, Server1_VN1).
- Servers can handle incoming requests and respond with their unique identifier.
- Written in Python using the `http.server` module for handling HTTP requests.

## Getting Started

To set up and run the load balancer and servers, follow these steps:

1. Clone the repository to your local machine.

2. Start docker: 

   ```bash
   sudo systemctl start docker
   ```

3. Run docker-compose:

   ```bash
   sudo docker-compose up --build
   ```


## Usage

### Load Balancer Endpoints

- To add Servers dynamically, send a POST request to the Load Balancer:

  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"n": 3, "hostnames": ["Server0", "Server1", "Server2"]}' http://localhost:5000/add
  ```

- To remove Servers dynamically, send a DELETE request to the Load Balancer:

  ```bash
  curl -X DELETE -H "Content-Type: application/json" -d '{"n": 2, "hostnames": ["Server0", "Server1"]}' http://localhost:5000/rm
  ```

- To fetch the list of active Servers, send a GET request to the Load Balancer:

  ```bash
  curl http://localhost:5000/get
  ```

### Client Requests

- Clients can send HTTP GET requests to the Load Balancer's root URL (http://localhost:5000/home).
- The Load Balancer will route the requests to the appropriate Server based on the consistent hashing algorithm.

## Testing

To test the load balancing system, you can use the provided `async_requester_a2.py` script to send a large number of requests to the Load Balancer and measure the distribution of requests among Servers.

## Customization

You can customize the number of Servers and virtual nodes per Server by modifying the `load_balancer.py` and `server.py` files.

## Contributors

- Saurav
- Sumit Dwivedi
- Rohan Patidar


