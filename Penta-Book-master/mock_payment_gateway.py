from flask import Flask, request, jsonify
import uuid
import random
import logging

app = Flask(__name__)

# Configuring logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In-memory store for payment activities
payment_history = []


# Endpoint to mimic payment processing
@app.route('/process_payment', methods=['POST'])
def process_payment():
    data = request.json
    logger.debug(f"Received payment request: {data}")

    if not data.get('amount') or not isinstance(data['amount'], (int, float)):
        return jsonify({"status": "failed", "message": "Missing or invalid amount"}), 400
    if not data.get('method_id'):
        return jsonify({"status": "failed", "message": "Missing method_id"}), 400
    if not data.get('order_id'):
        return jsonify({"status": "failed", "message": "Missing order_id"}), 400

    # Simulate transaction processing
    transaction_id = str(uuid.uuid4())
    payment_status = simulate_payment_status(data['method_id'])

    response = {
        "transaction_id": transaction_id,
        "payment_status": payment_status,
        "method_id": data['method_id'],
        "order_id": data['order_id']
    }

    # Record transaction in history
    payment_history.append(response)
    logger.info(f"Processed payment: {response}")

    if payment_status == 'approved':
        return jsonify({"status": "success", "data": response}), 200
    else:
        return jsonify({"status": "failed", "data": response, "message": "Payment was declined"}), 400


def simulate_payment_status(method_id):
    """ Simulate different payment behaviors based on method_id """
    if method_id == 'credit_card':
        return random.choice(['approved', 'declined'])
    elif method_id == 'paypal':
        return random.choice(['approved', 'declined', 'pending'])
    # Add more methods as needed
    else:
        return 'declined'


@app.route('/payment_history', methods=['GET'])
def get_payment_history():
    return jsonify({"status": "success", "data": payment_history}), 200


if __name__ == '__main__':
    app.run(port=5001, debug=True)
