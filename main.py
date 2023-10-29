import asyncio
import websockets
import json
import logging
import redis
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
REDIS_IP = os.getenv("REDIS_IP", "localhost")
redis_client = redis.Redis(host=REDIS_IP, port=6379, db=0)
connected_clients = []

async def load_messages_by_id(chat_id):
    messages = redis_client.lrange(f"messages:{chat_id}", 0, -1)
    return [json.loads(message.decode('utf-8')) for message in messages]

async def echo(websocket, path):
    connected_clients.append(websocket)
    try:
        print("Client connected")
        async for message in websocket:
            data = json.loads(message)
            print(f"Raw message received: {message}")
            sender_id = data.get("sender_id", "")
            receiver_id = data.get("receiver_id", "")
            chat_id = "_".join(sorted([sender_id, receiver_id]))

            if 'command' in data:
                if data['command'] == 'load_messages':
                    messages = await load_messages_by_id(chat_id)
                    await websocket.send(json.dumps({'command': 'load_messages', 'messages': messages}))
                    continue
                elif data['command'] == 'accept_request':
                    redis_client.set(f"chat_requests:{chat_id}", "accepted")
                    continue
                elif data['command'] == 'reject_request':
                    redis_client.set(f"chat_requests:{chat_id}", "rejected")
                    continue

            if 'text' not in data:
                print("Missing 'text' key in received data")
                continue

            message_data = {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "text": data["text"],
                "status": "pending",
            }
            redis_client.rpush(f"messages:{chat_id}", json.dumps(message_data))
            print(f"Message stored: {data['text']}")

            for client in connected_clients:
                await client.send(message)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connected_clients.remove(websocket)


start_server = websockets.serve(echo, "0.0.0.0", 5678)
print("Server started on ws://0.0.0.0:5678")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()