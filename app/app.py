import logging
import uuid
import re
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [%(request_id)s] %(message)s')
logger = logging.getLogger(__name__)

orders_db = {}


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(request, 'request_id', 'no-req-id')
        return True


logger.addFilter(RequestIDFilter())


@app.before_request
def before_request():
    request.request_id = str(uuid.uuid4())[:8]
    logger.info(f"Incoming {request.method} {request.path}")


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_order_data(data):
    errors = []
    if not data:
        return ['Request body is required']

    if 'customer_email' not in data:
        errors.append('customer_email is required')
    elif not validate_email(data['customer_email']):
        errors.append('customer_email must be a valid email address')

    if 'amount' not in data:
        errors.append('amount is required')
    else:
        try:
            amount = float(data['amount'])
            if amount <= 0:
                errors.append('amount must be greater than 0')
        except (ValueError, TypeError):
            errors.append('amount must be a valid number')

    if 'items' not in data or not isinstance(data['items'], list) or len(data['items']) == 0:
        errors.append('items must be a non-empty list')

    return errors


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'orders', 'version': '1.0.0'}), 200


@app.route('/orders', methods=['GET'])
def list_orders():
    try:
        orders = [{'order_id': oid, **d} for oid, d in orders_db.items()]
        return jsonify({'orders': orders}), 200
    except Exception as e:
        logger.error(f"Error listing orders: {e}")
        return jsonify({'error': 'Failed to list orders'}), 500


@app.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        errors = validate_order_data(data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400

        order_id = str(uuid.uuid4())
        orders_db[order_id] = {
            'customer_email': data['customer_email'],
            'amount': float(data['amount']),
            'items': data['items'],
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        logger.info(f"Created order {order_id}")
        return jsonify({'order_id': order_id, **orders_db[order_id]}), 201
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({'error': 'Failed to create order'}), 500


@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    if order_id not in orders_db:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'order_id': order_id, **orders_db[order_id]}), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)  # nosec B104
