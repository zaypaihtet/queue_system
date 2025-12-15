import os
from moceansdk import Client, Basic
import logging
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from ai_predictor import AIWaitTimePredictor
from models import DatabaseManager, Customer, Analytics
from wait_time_updater import WaitTimeUpdater
import qrcode
from io import BytesIO
import base64

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)  # Enable CORS for all routes

# Initialize AI predictor and database
ai_predictor = AIWaitTimePredictor()
db_manager = DatabaseManager()
customer_model = Customer(db_manager)
analytics_model = Analytics(db_manager)
wait_time_updater = WaitTimeUpdater(db_manager)

MOCEAN_API_KEY = "apit-szNDiHceZLxM1ggtNSaRWaF2hhDB79In-ymRER"
MOCEAN_API_SECRET = "YOUR_API_SECRET"

# Initialize Mocean client
mocean = Client(Basic(MOCEAN_API_KEY, MOCEAN_API_SECRET))
@app.route('/send_sms', methods=['POST'])
def send_sms():
    try:
        data = request.get_json()
        to_number = data.get("to")
        text_message = data.get("message")

        if not to_number or not text_message:
            return jsonify({"status": "error", "message": "Missing 'to' or 'message'"}), 400

        command = f'''curl -X POST "https://rest.moceanapi.com/rest/2/sms" \
           -H "Authorization: Bearer apit-szNDiHceZLxM1ggtNSaRWaF2hhDB79In-ymRER" \
           -d "mocean-from=MOCEAN" \
           -d "mocean-to={to_number}" \
           -d "mocean-text={text_message}"'''

        os.system(command)

        return jsonify({
            "status": "success",
            "to": to_number,
            "message": text_message,
            "info": "SMS sent successfully via Mocean API"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500





@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/status')
def customer_status():
    """Customer status checking page"""
    return render_template('customer_status.html')

@app.route('/api/queue', methods=['GET'])
def get_queue():
    """API endpoint to get current queue from database"""
    try:
        customers = customer_model.get_all()
        # Convert database format to frontend format
        queue_data = []
        for customer in customers:
            queue_data.append({
                'id': customer['id'],
                'queueNumber': customer['queue_number'],
                'customerName': customer['customer_name'],
                'phone': customer['phone'],
                'partySize': customer['party_size'],
                'queueType': customer['queue_type'],
                'status': customer['status'],
                'timestamp': customer['timestamp'],
                'estimatedWait': customer['estimated_wait'],
                'aiPowered': customer['ai_powered'],
                'confidence': customer['confidence'],
                'aiFactors': customer['ai_factors']
            })
        return jsonify(queue_data)
    except Exception as e:
        logging.error(f"Error fetching queue: {e}")
        return jsonify([])

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """API endpoint to get analytics data from database"""
    try:
        stats = customer_model.get_queue_stats()
        
        # Get today's date for analytics
        today = datetime.now().strftime('%Y-%m-%d')
        daily_analytics = analytics_model.get_analytics_by_date(today)
        
        analytics_data = {
            'today_customers': stats['today_total'],
            'average_wait_time': stats['avg_wait_time'],
            'peak_hour': daily_analytics['peak_hour'] if daily_analytics else '12:00 PM',
            'queue_efficiency': daily_analytics['efficiency_score'] if daily_analytics else 85,
            'hourly_data': daily_analytics['hourly_data'] if daily_analytics else [5, 8, 12, 18, 25, 30, 35, 42, 38, 28, 15, 10],
            'wait_time_data': [15, 20, 18, 22, 16, 19, 21, 17, 14, 25, 23, 18]  # Could be calculated from actual data
        }
        
        return jsonify(analytics_data)
    except Exception as e:
        logging.error(f"Error fetching analytics: {e}")
        return jsonify({
            'today_customers': 0,
            'average_wait_time': 0,
            'peak_hour': '12:00 PM',
            'queue_efficiency': 0,
            'hourly_data': [],
            'wait_time_data': []
        })

@app.route('/api/predict-wait-time', methods=['POST'])
def predict_wait_time():
    """AI-powered wait time prediction endpoint"""
    try:
        data = request.get_json()
        
        # Get current queue data
        current_queue = data.get('queue_data', [])
        customer_data = data.get('customer_data', {})
        
        # Use AI to predict wait time
        prediction = ai_predictor.predict_wait_time(
            queue_data=current_queue,
            customer_data=customer_data
        )
        
        return jsonify(prediction)
        
    except Exception as e:
        logging.error(f"Wait time prediction error: {e}")
        return jsonify({
            "estimated_wait": 20,
            "confidence": 50,
            "factors": ["Error in AI prediction"],
            "recommendation": "Using fallback calculation",
            "ai_powered": False
        })

@app.route('/api/queue-insights', methods=['POST'])
def get_queue_insights():
    """Simple queue efficiency analysis"""
    try:
        data = request.get_json()
        queue_data = data.get('queue_data', [])
        
        # Simple analysis without AI for faster response
        waiting_count = len([c for c in queue_data if c.get('status') == 'Waiting'])
        seated_count = len([c for c in queue_data if c.get('status') == 'Seated'])
        
        # Basic efficiency calculation
        total_customers = len(queue_data)
        efficiency_score = max(60, min(90, 85 - (waiting_count * 5)))
        
        avg_wait = 15 if waiting_count < 3 else 25 if waiting_count < 6 else 35
        
        return jsonify({
            "efficiency_score": efficiency_score,
            "avg_wait_time": avg_wait,
            "bottlenecks": ["Normal operations"] if waiting_count < 5 else ["High queue volume"],
            "suggestions": ["Continue monitoring"] if waiting_count < 5 else ["Consider additional staff"],
            "peak_hour_prediction": "Standard service patterns"
        })
        
    except Exception as e:
        logging.error(f"Queue insights error: {e}")
        return jsonify({
            "efficiency_score": 75,
            "avg_wait_time": 20,
            "bottlenecks": ["Analysis unavailable"],
            "suggestions": ["Monitor queue regularly"],
            "peak_hour_prediction": "Standard patterns expected"
        })

@app.route('/api/customers', methods=['POST'])
def add_customer():
    """Add a new customer to the queue"""
    try:
        data = request.get_json()
        
        queue_type = data.get('queue_type')
        prefix = 'T' if queue_type == 'Table' else 'K'

        customers = customer_model.get_all()
        existing_numbers = [
            int(c['queue_number'][1:]) for c in customers if c['queue_number'].startswith(prefix)
        ]
        next_num = max(existing_numbers, default=0) + 1
        queue_number = f"{prefix}{str(next_num).zfill(3)}"
        # Get real-time wait time estimate
        party_size = data.get('party_size', 1)
        estimated_wait = wait_time_updater.get_real_time_wait_estimate(queue_type, party_size)
        
        prediction = {
            'estimated_wait': estimated_wait,
            'confidence': 90,
            'ai_powered': False,
            'factors': [f"Real-time calculation based on current queue position", f"{queue_type} service pattern", "Automatically updates when queue changes"]
        }
        
        # Create customer record
        customer_id = customer_model.create(
            queue_number=queue_number,
            customer_name=data.get('customer_name'),
            phone=data.get('phone'),
            party_size=data.get('party_size'),
            queue_type=data.get('queue_type'),
            estimated_wait=prediction.get('estimated_wait', 20),
            confidence=prediction.get('confidence'),
            ai_powered=prediction.get('ai_powered', False),
            ai_factors=prediction.get('factors')
        )
        
        # Trigger wait time updates for all other customers
        wait_time_updater.trigger_wait_time_update('customer_added')
        
        return jsonify({
            'success': True,
            'customer_id': customer_id,
            'queue_number': queue_number,
            'prediction': prediction
        })
        
    except Exception as e:
        logging.error(f"Error adding customer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>/status', methods=['PUT'])
def update_customer_status(customer_id):
    """Update customer status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        success = customer_model.update_status(customer_id, new_status)
        
        if success:
            # Trigger wait time updates when status changes (affects queue position)
            wait_time_updater.trigger_wait_time_update(f'status_changed_to_{new_status}')
        
        return jsonify({'success': success})
        
    except Exception as e:
        logging.error(f"Error updating customer status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete customer from queue"""
    try:
        success = customer_model.delete(customer_id)
        return jsonify({'success': success})
        
    except Exception as e:
        logging.error(f"Error deleting customer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/search', methods=['GET'])
def search_customers():
    """Search customers by name or phone"""
    try:
        search_term = request.args.get('q', '')
        customers = customer_model.search(search_term)
        
        # Convert to frontend format
        queue_data = []
        for customer in customers:
            queue_data.append({
                'id': customer['id'],
                'queueNumber': customer['queue_number'],
                'customerName': customer['customer_name'],
                'phone': customer['phone'],
                'partySize': customer['party_size'],
                'queueType': customer['queue_type'],
                'status': customer['status'],
                'timestamp': customer['timestamp'],
                'estimatedWait': customer['estimated_wait'],
                'aiPowered': customer['ai_powered'],
                'confidence': customer['confidence'],
                'aiFactors': customer['ai_factors']
            })
        
        return jsonify(queue_data)
        
    except Exception as e:
        logging.error(f"Error searching customers: {e}")
        return jsonify([]), 500

@app.route('/api/queue/stats', methods=['GET'])
def get_queue_stats():
    """Get real-time queue statistics"""
    try:
        stats = customer_model.get_queue_stats()
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error fetching queue stats: {e}")
        return jsonify({
            'waiting_count': 0,
            'seated_count': 0,
            'done_count': 0,
            'avg_wait_time': 0,
            'today_total': 0
        }), 500

@app.route('/api/customer/status/<queue_number>', methods=['GET'])
def get_customer_status(queue_number):
    """Get customer status by queue number for customer-facing page"""
    try:
        # Find customer by queue number
        customers = customer_model.get_all()
        customer = None
        for c in customers:
            if c['queue_number'] == queue_number:
                customer = c
                break
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Calculate position in queue
        waiting_customers = [c for c in customers if c['status'] == 'Waiting']
        waiting_customers.sort(key=lambda x: x['created_at'])
        
        position = 0
        if customer['status'] == 'Waiting':
            for i, c in enumerate(waiting_customers):
                if c['id'] == customer['id']:
                    position = i
                    break
        
        return jsonify({
            'queueNumber': customer['queue_number'],
            'customerName': customer['customer_name'],
            'partySize': customer['party_size'],
            'queueType': customer['queue_type'],
            'status': customer['status'],
            'estimatedWait': customer['estimated_wait'],
            'position': position,
            'timestamp': customer['timestamp']
        })
        
    except Exception as e:
        logging.error(f"Error getting customer status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/customer/<int:customer_id>/qr', methods=['GET'])
def generate_customer_qr(customer_id):
    """Generate QR code for customer status checking"""
    try:
        customer = customer_model.get_by_id(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Create QR code URL
        base_url = request.url_root.rstrip('/')
        status_url = f"{base_url}/status?queue={customer['queue_number']}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(status_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_data = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'qr_code': f"data:image/png;base64,{qr_data}",
            'status_url': status_url,
            'queue_number': customer['queue_number']
        })
        
    except Exception as e:
        logging.error(f"Error generating QR code: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
