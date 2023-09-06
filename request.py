from flask import Flask, request, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)

# Replace this with your actual MongoDB connection URL
app.config["MONGO_URI"] = "mongodb+srv://bohfyrms:bohfyrms@cluster0.buhlpyd.mongodb.net/test"
mongo = PyMongo(app)
db = mongo.db

@app.route('/get_all_messages', methods=['GET'])
def get_all_messages():
    sender_id = request.args.get('sender_id')
    receiver_id = request.args.get('receiver_id')

    # Find all messages where the given sender and receiver are involved
    matching_messages = db.messages.find({
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id},
        ]
    })

    # Convert the matching messages to a list of dictionaries
    result = [{
        "sender_id": msg["sender_id"],
        "receiver_id": msg["receiver_id"],
        "text": msg["text"],
        "timestamp": msg.get("timestamp")  # Using .get() to safely retrieve the timestamp value, if it exists
    } for msg in matching_messages]

    return jsonify(result), 200



@app.route('/send_request', methods=['POST'])
def send_request():
    sender_id = request.json['sender_id']
    receiver_id = request.json['receiver_id']

    # Create a new request with status "pending"
    db.requests.insert_one({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "status": "pending",
    })
    return jsonify({"status": "pending"}), 200

@app.route('/get_requests_by_sender_id_and_receiver_id', methods=['GET'])
def get_requests_by_sender_id_and_receiver_id():
    sender_id = request.args.get('sender_id')
    receiver_id = request.args.get('receiver_id')

    # Find all requests where the given sender and receiver are involved
    matching_requests = db.requests.find({
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id},
        ]
    })

    # Convert the matching requests to a list of dictionaries without ObjectId
    result = [{
        "sender_id": req["sender_id"],
        "receiver_id": req["receiver_id"],
        "status": req["status"]
    } for req in matching_requests]

    return jsonify(result), 200

@app.route('/get_all_requests', methods=['GET'])
def get_all_requests():
    # Fetch all requests from the database
    all_requests = db.requests.find()

    # Convert the fetched requests to a list of dictionaries
    result = [{
        "sender_id": req["sender_id"],
        "receiver_id": req["receiver_id"],
        "status": req["status"]
    } for req in all_requests]

    return jsonify(result), 200



@app.route('/accept_request', methods=['POST'])
def accept_request():
    sender_id = request.json['sender_id']
    receiver_id = request.json['receiver_id']

    # Find the existing request and update its status to "accepted"
    existing_request = db.requests.find_one({
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id},
        ]
    })
    if existing_request:
        db.requests.update_one({"_id": existing_request["_id"]}, {"$set": {"status": "accepted"}})
        return jsonify({"status": "accepted"}), 200
    else:
        return jsonify({"error": "Request not found"}), 404

@app.route('/reject_request', methods=['POST'])
def reject_request():
    sender_id = request.json['sender_id']
    receiver_id = request.json['receiver_id']

    # Find the existing request and update its status to "rejected"
    existing_request = db.requests.find_one({
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id},
        ]
    })
    if existing_request:
        db.requests.update_one({"_id": existing_request["_id"]}, {"$set": {"status": "rejected"}})
        return jsonify({"status": "rejected"}), 200
    else:
        return jsonify({"error": "Request not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)  # You can choose a different port if needed
