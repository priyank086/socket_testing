# Import required libraries
import asyncio
import websockets
import json
import logging
import redis
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set up logging with INFO level
logging.basicConfig(level=logging.INFO)

# Get the Redis IP from environment variables or use "localhost" as default
REDIS_IP = os.getenv("REDIS_IP", "localhost")

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_IP, port=6379, db=0)

# List to keep track of connected WebSocket clients
connected_clients = []

# Asynchronous function to load messages by chat ID from Redis
async def load_messages_by_id(chat_id):
    messages = redis_client.lrange(f"messages:{chat_id}", 0, -1)
    return [json.loads(message.decode('utf-8')) for message in messages]

# Asynchronous function to handle WebSocket connections
async def echo(websocket, path):
    # Add the connected WebSocket client to the list
    connected_clients.append(websocket)
    try:
        print("Client connected")
        # Loop to handle incoming messages from the WebSocket
        async for message in websocket:
            # Parse the incoming message as JSON
            data = json.loads(message)
            print(f"Raw message received: {message}")

            # Extract sender and receiver IDs from the message
            sender_id = data.get("sender_id", "")
            receiver_id = data.get("receiver_id", "")
            # Generate a chat ID by sorting and joining the sender and receiver IDs
            chat_id = "_".join(sorted([sender_id, receiver_id]))

            # Check for special commands in the message
            if 'command' in data:
                # Handle the 'load_messages' command
                if data['command'] == 'load_messages':
                    messages = await load_messages_by_id(chat_id)
                    await websocket.send(json.dumps({'command': 'load_messages', 'messages': messages}))
                
                # Handle the 'accept_request' command
                elif data['command'] == 'accept_request':
                    redis_client.set(f"chat_requests:{chat_id}", "accepted")
                
                # Handle the 'reject_request' command
                elif data['command'] == 'reject_request':
                    redis_client.set(f"chat_requests:{chat_id}", "rejected")

                # Handle the 'order_complete' command
                elif data['command'] == 'order_complete':
                    print(f"Order Complete command received with payment ID: {data['payment_id']}")
                

            # Check if the 'text' key exists in the message
            if 'text' not in data:
                print("Missing 'text' key in received data")
                continue

            # Create a dictionary to store the message data
            message_data = {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "text": data["text"],
                "status": "pending",
            }
            # Store the message in Redis
            redis_client.rpush(f"messages:{chat_id}", json.dumps(message_data))
            print(f"Message stored: {data['text']}")

            # Broadcast the message to all connected clients
            for client in connected_clients:
                await client.send(message)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Remove the WebSocket client from the list when disconnected
        connected_clients.remove(websocket)

# Start the WebSocket server
start_server = websockets.serve(echo, "0.0.0.0", 5678)
print("Server started on ws://0.0.0.0:5678")

# Run the WebSocket server
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
