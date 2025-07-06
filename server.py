from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# Aseguramos que exista el directorio results
RESULTS_DIR = "feedback"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

DATA_FILE = os.path.join(RESULTS_DIR, "interactions.json")

@app.route("/slack/interactive-endpoint", methods=["POST"])
def slack_interactive():
    # Slack envía los datos como form-urlencoded, extraemos el payload
    form_data = request.form
    payload = json.loads(form_data["payload"])  # Convertimos a JSON

    print("Interacción recibida:", payload)

    # Create file if it doesn't exist
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            json.dump([], f)

    # Read existing data
    try:
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = []

    # Get unique identifier from payload
    message_ts = payload.get('container', {}).get('message_ts')
    user_id = payload.get('user', {}).get('id')
    interaction_id = f"{user_id}_{message_ts}"

    # Check if interaction with same ID exists
    existing_interaction_index = None
    for index, item in enumerate(data):
        item_message_ts = item.get('container', {}).get('message_ts')
        item_user_id = item.get('user', {}).get('id')
        item_interaction_id = f"{item_user_id}_{item_message_ts}"
        
        if item_interaction_id == interaction_id:
            existing_interaction_index = index
            break

    # Update existing or append new
    if existing_interaction_index is not None:
        data[existing_interaction_index] = payload
    else:
        data.append(payload)

    # Write back all data
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, default=str)

    return jsonify({"status": "ok"})  # Responder a Slack

if __name__ == "__main__":
    app.run(port=5000)


#This is the url of the server of the commando ngrok http 5000
#https://e15a-190-247-144-103.ngrok-free.app/slack/interactive-endpoint