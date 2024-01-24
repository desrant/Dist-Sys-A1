import asyncio
import aiohttp
import json
import time

async def fetch(session, url, i):
    # Modify the request path by appending a unique query parameter
    async with session.get(f"{url}?query={i}") as response:
        return await response.read(), response.status

async def main():
    url = "http://localhost:5000/home"
    tasks = []
    async with aiohttp.ClientSession() as session:
        for i in range(10000):  # Number of requests
            # Pass the unique identifier `i` to the fetch function
            task = asyncio.ensure_future(fetch(session, url, i))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        # Count the responses from each server
        server_counts = {}
        for response, status in responses:
            if status == 200:
                server_id = json.loads(response.decode('utf-8'))['message'].split()[-1]
                server_counts[server_id] = server_counts.get(server_id, 0) + 1
        print(server_counts)

if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    duration = time.time() - start_time
    print(f"Sent 10000 requests in {duration} seconds")
