"""
Webhook handler for NOWPayments + Razorpay
✅ FIXED: Proper import handling
"""

from flask import Flask, request, jsonify
import logging
import sys
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('webhook.log')
    ]
)
logger = logging.getLogger(__name__)

# Import config
try:
    import config
    logger.info("✅ Config imported")
except Exception as e:
    logger.error(f"❌ Config import failed: {e}")
    sys.exit(1)

# Import payment handlers
try:
    from payment_nowpayments import process_ipn_callback
    logger.info("✅ NOWPayments handler imported")
except Exception as e:
    logger.warning(f"⚠️ NOWPayments import failed: {e}")
    process_ipn_callback = None

# Initialize Razorpay - CRITICAL FIX
RAZORPAY_ENABLED = False
razorpay_client = None

try:
    import razorpay
    
    # Check credentials
    if not hasattr(config, 'RAZORPAY_KEY_ID') or not config.RAZORPAY_KEY_ID:
        logger.error("❌ RAZORPAY_KEY_ID not in config")
        RAZORPAY_ENABLED = False
    elif not hasattr(config, 'RAZORPAY_KEY_SECRET') or not config.RAZORPAY_KEY_SECRET:
        logger.error("❌ RAZORPAY_KEY_SECRET not in config")
        RAZORPAY_ENABLED = False
    else:
        razorpay_client = razorpay.Client(
            auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET)
        )
        RAZORPAY_ENABLED = True
        logger.info("✅ Razorpay initialized")
        
except ImportError:
    logger.warning("⚠️ razorpay module not installed")
    RAZORPAY_ENABLED = False
except Exception as e:
    logger.error(f"❌ Razorpay init failed: {e}")
    RAZORPAY_ENABLED = False

app = Flask(__name__)

@app.route('/razorpay/webhook', methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay webhook"""
    if not RAZORPAY_ENABLED:
        logger.error("❌ Razorpay not configured")
        return jsonify({'status': 'error', 'message': 'Razorpay not configured'}), 503
    
    try:
        logger.info("🔥 RAZORPAY WEBHOOK")
        
        webhook_data = request.get_json()
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        
        if not webhook_data:
            return jsonify({'status': 'error'}), 400
        
        if not webhook_signature:
            return jsonify({'status': 'error'}), 400
        
        event = webhook_data.get('event', 'unknown')
        logger.info(f"📦 Event: {event}")
        
        # Verify signature
        razorpay_client.utility.verify_webhook_signature(
            request.get_data().decode('utf-8'),
            webhook_signature,
            config.RAZORPAY_KEY_SECRET
        )
        logger.info("✅ Signature verified")
        
        # Import handler
        from payment_razorpay import process_payment_success, process_payment_failed
        
        if event == 'payment_link.paid':
            payment_link = webhook_data.get('payload', {}).get('payment_link', {}).get('entity', {})
            payment_link_id = payment_link.get('id')
            payments = payment_link.get('payments', [])
            payment_id = payments[0].get('payment_id') if payments else None
            
            logger.info(f"💰 Payment: {payment_link_id}")
            success = process_payment_success(payment_link_id, payment_id)
            
            return jsonify({'status': 'success' if success else 'failed'}), 200
        
        elif event == 'payment_link.cancelled':
            payment_link = webhook_data.get('payload', {}).get('payment_link', {}).get('entity', {})
            order_id = payment_link.get('id')
            process_payment_failed(order_id)
            return jsonify({'status': 'acknowledged'}), 200
        
        elif event == 'payment.captured':
            payment = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment.get('order_id')
            payment_id = payment.get('id')
            
            logger.info(f"💰 Captured: {order_id}")
            success = process_payment_success(order_id, payment_id)
            
            return jsonify({'status': 'success' if success else 'failed'}), 200
        
        elif event == 'payment.failed':
            payment = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment.get('order_id')
            process_payment_failed(order_id)
            return jsonify({'status': 'acknowledged'}), 200
        
        else:
            return jsonify({'status': 'acknowledged'}), 200
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error'}), 500

@app.route('/nowpayments/webhook', methods=['POST'])
def nowpayments_webhook():
    """Handle NOWPayments"""
    if not process_ipn_callback:
        return jsonify({'status': 'error'}), 503
    
    try:
        logger.info("🔥 NOWPAYMENTS WEBHOOK")
        
        signature = request.headers.get('x-nowpayments-sig', '')
        ipn_data = request.get_json()
        
        if not signature or not ipn_data:
            return jsonify({'status': 'error'}), 400
        
        success = process_ipn_callback(ipn_data, signature)
        return jsonify({'status': 'ok' if success else 'error'}), 200
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'razorpay': RAZORPAY_ENABLED,
        'nowpayments': process_ipn_callback is not None
    }), 200

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'running',
        'razorpay': RAZORPAY_ENABLED,
        'nowpayments': process_ipn_callback is not None
    }), 200

if __name__ == '__main__':
    logger.info("🚀 WEBHOOK HANDLER")
    logger.info(f"Razorpay: {'✅' if RAZORPAY_ENABLED else '❌'}")
    logger.info(f"NOWPayments: {'✅' if process_ipn_callback else '❌'}")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
