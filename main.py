import asyncio
import websockets
import json
import logging
import redis

logging.basicConfig(level=logging.INFO)

# Cache to store the status of the first message for each chat
chat_status_cache = {}

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# List to keep track of connected clients
connected_clients = []

async def echo(websocket, path):
    connected_clients.append(websocket)
    try:
        logging.info("Client connected")

        async for message in websocket:
            data = json.loads(message)

            # Store the message in Redis
            message_data = {
                "sender_id": data["sender_id"],
                "receiver_id": data["receiver_id"],
                "text": data["text"],
                "status": "pending",
            }
            redis_client.rpush(f"messages:{data['chat_id']}", json.dumps(message_data))

            logging.info(f"Message stored: {data['text']}")

            # Broadcast the message to all connected clients
            for client in connected_clients:
                await client.send(message)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        connected_clients.remove(websocket)

# Start the WebSocket server
start_server = websockets.serve(echo, "0.0.0.0", 5678)
logging.info("Server started on ws://0.0.0.0:5678")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
