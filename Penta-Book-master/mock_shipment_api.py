from flask import Flask, request, jsonify
import uuid
import random
import logging

app = Flask(__name__)

# Configuring logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In-memory store for shipment activities
shipment_history = []


# Endpoint to mimic shipment processing
@app.route('/create_shipment', methods=['POST'])
def create_shipment():
    data = request.json
    logger.debug(f"Received shipment request: {data}")

    if not data.get('order_id'):
        return jsonify({"status": "failed", "message": "Missing order_id"}), 400
    if not data.get('address'):
        return jsonify({"status": "failed", "message": "Missing address"}), 400

    # Simulate shipment creation
    shipment_id = str(uuid.uuid4())
    shipment_status = "created"

    response = {
        "shipment_id": shipment_id,
        "shipment_status": shipment_status,
        "order_id": data['order_id'],
        "address": data['address']
    }

    # Record shipment in history
    shipment_history.append(response)
    logger.info(f"Processed shipment: {response}")

    return jsonify({"status": "success", "data": response}), 200


@app.route('/shipment_status/<shipment_id>', methods=['GET'])
def shipment_status(shipment_id):
    logger.debug(f"Received status request for shipment_id: {shipment_id}")

    for shipment in shipment_history:
        if shipment['shipment_id'] == shipment_id:
            return jsonify({"status": "success", "data": shipment}), 200

    return jsonify({"status": "failed", "message": "Shipment not found"}), 404


@app.route('/shipment_history', methods=['GET'])
def get_shipment_history():
    return jsonify({"status": "success", "data": shipment_history}), 200


if __name__ == '__main__':
    app.run(port=5002, debug=True)
