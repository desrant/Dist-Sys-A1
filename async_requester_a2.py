import asyncio
import aiohttp
import json
import time

async def fetch(session, url, params):
    async with session.get(url, params=params) as response:
        return await response.text(), response.status

async def run_test(num_servers):
    url = "http://localhost:5000/home"
    tasks = []
    timeout = aiohttp.ClientTimeout(total=60)  # Total timeout for the whole operation
    async with aiohttp.ClientSession() as session:
        for i in range(10000):  # Number of requests
            task = asyncio.ensure_future(fetch(session, url, params={'i': i}))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        server_counts = {}
        for response, status in responses:
            if status == 200:
                server_id = json.loads(response)['message'].split()[-1]
                server_counts[server_id] = server_counts.get(server_id, 0) + 1
        # Calculate the average load
        total_requests = sum(server_counts.values())
        average_load = total_requests / num_servers
        return average_load

async def main():
    N_values = [5]
    average_loads = []
    for N in N_values:
        average_load = await run_test(N)
        average_loads.append(average_load)
    return N_values, average_loads

if __name__ == '__main__':
    start_time = time.time()
    N_values, average_loads = asyncio.run(main())
    duration = time.time() - start_time
    print(f"Test completed in {duration} seconds")
    print("N_values:", N_values)
    print("Average loads:", average_loads)
