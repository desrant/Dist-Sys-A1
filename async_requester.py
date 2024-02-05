import asyncio
import aiohttp
import json
import time

async def fetch(session, url, i, timeout=30):
    try:
        async with session.get(f"{url}?query={i}", timeout=timeout) as response:
            return await response.read(), response.status
    except asyncio.TimeoutError as e:
        # Handle the timeout exception (e.g., print an error message)
        print(f"Timeout error for query {i}: {e}")
        return None, None
    except aiohttp.ClientError as e:
        # Handle other client errors
        print(f"Client error for query {i}: {e}")
        return None, None

async def main():
    url = "http://localhost:5000/home"
    tasks = []
    async with aiohttp.ClientSession() as session:
        for i in range(10000):  # Number of requests
            task = asyncio.ensure_future(fetch(session, url, i))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)

        # Count the responses from each server
        server_counts = {}
        for response, status in responses:
            if status == 200:
                server_id = json.loads(response.decode('utf-8'))['message'].split()[-1]
                # print(server_id)
                server_counts[server_id[:-4]] = server_counts.get(server_id[:-4], 0) + 1
            elif status is not None:
                print(f"Request for query {i} failed with status code {status}")
        # print("Timed out packets:",10000-len(responses))
        # print("Average Server Load:",total_response/len(server_counts))
        print(server_counts)

if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    duration = time.time() - start_time
    print(f"Sent 10000 requests in {duration} seconds")
