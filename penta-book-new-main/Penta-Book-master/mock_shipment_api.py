from flask import Flask, request, jsonify
import sqlite3
import random
import datetime

app = Flask(__name__)


def get_db():
    db = sqlite3.connect('penta_book.db')  # Update this path
    db.row_factory = sqlite3.Row
    return db


@app.route('/initiate_shipment', methods=['POST'])
def initiate_shipment():
    order_id = request.json.get('order_id')
    shipment_service = request.json.get('shipment_service', 'default_service')

    db = get_db()
    try:
        # Check if the order exists
        order = db.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchone()
        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found.'}), 404

        # Generate a mock tracking number
        tracking_no = 'TRK' + str(random.randint(100000, 999999))

        # Create shipment entry
        db.execute('''
            INSERT INTO shipment (order_id, tracking_no, shipment_date, status, shipment_service)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, tracking_no, datetime.datetime.now().isoformat(), 'Shipped', shipment_service))
        db.commit()

        return jsonify({'status': 'success', 'tracking_no': tracking_no}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()


@app.route('/track_shipment/<tracking_no>', methods=['GET'])
def track_shipment(tracking_no):
    db = get_db()
    try:
        shipment = db.execute('SELECT * FROM shipment WHERE tracking_no = ?', (tracking_no,)).fetchone()
        if not shipment:
            return jsonify({'status': 'error', 'message': 'Shipment not found.'}), 404

        return jsonify({
            'status': 'success',
            'shipment_data': {
                'tracking_no': shipment['tracking_no'],
                'order_id': shipment['order_id'],
                'shipment_date': shipment['shipment_date'],
                'received_date': shipment['received_date'],
                'status': shipment['status'],
                'shipment_service': shipment['shipment_service']
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()


if __name__ == '__main__':
    app.run(port=5002, debug=True)  # Running on a different port than the Flask app