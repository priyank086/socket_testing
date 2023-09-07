import asyncio
import websockets
import json
import logging
import redis
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Redis setup
REDIS_IP = os.getenv("REDIS_IP", "localhost")
redis_client = redis.Redis(host=REDIS_IP, port=6379, db=0)

# List to keep track of connected clients
connected_clients = []

async def echo(websocket, path):
    connected_clients.append(websocket)
    try:
        logging.info("Client connected")

        async for message in websocket:
            try:
                data = json.loads(message)
                logging.info(f"Received data: {data}")

                if 'text' not in data:
                    logging.error("Missing 'text' key in received data")
                    continue

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

            except json.JSONDecodeError:
                logging.error("Received message is not a valid JSON")
            except KeyError as e:
                logging.error(f"Missing key in received data: {e}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    finally:
        connected_clients.remove(websocket)

# Start the WebSocket server
start_server = websockets.serve(echo, "0.0.0.0", 5678)

logging.info("Server started on ws://0.0.0.0:5678")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()