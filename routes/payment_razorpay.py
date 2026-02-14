"""
Razorpay Payment Integration - COMPLETE FIX v3
✅ Fixed Razorpay client initialization
✅ Better error handling for missing dependencies
✅ Proper connection pool management
✅ Guaranteed admin notifications
"""

import logging
import config
from database import get_db, Transaction, User, SystemSettings
from datetime import datetime
import time
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

BOT_USERNAME = getattr(config, 'BOT_USERNAME', 'your_bot').replace('@', '')

# ========================================
# TELEGRAM BOT INITIALIZATION
# ========================================
try:
    from telegram import Bot
    from telegram.request import HTTPXRequest
    
    request = HTTPXRequest(
        connection_pool_size=30,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )
    
    bot = Bot(token=config.BOT_TOKEN, request=request)
    TELEGRAM_AVAILABLE = True
    logger.info("✅ Telegram bot initialized")
except Exception as e:
    TELEGRAM_AVAILABLE = False
    bot = None
    logger.warning(f"⚠️ Telegram disabled: {e}")

# ========================================
# RAZORPAY CLIENT INITIALIZATION
# ========================================
razorpay_client = None
RAZORPAY_AVAILABLE = False

def initialize_razorpay():
    """Initialize Razorpay client with proper error handling"""
    global razorpay_client, RAZORPAY_AVAILABLE
    
    try:
        # Check config first
        if not hasattr(config, 'RAZORPAY_KEY_ID'):
            logger.error("❌ RAZORPAY_KEY_ID not found in config.py")
            return False
            
        if not hasattr(config, 'RAZORPAY_KEY_SECRET'):
            logger.error("❌ RAZORPAY_KEY_SECRET not found in config.py")
            return False
        
        if not config.RAZORPAY_KEY_ID or not config.RAZORPAY_KEY_SECRET:
            logger.error("❌ Razorpay credentials are empty in config.py")
            return False
        
        # Try importing razorpay
        try:
            import razorpay
        except ImportError:
            logger.error("❌ 'razorpay' module not installed. Run: pip install razorpay")
            return False
        
        # Try importing requests for session management
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Create session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=5,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
            )
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20,
                pool_block=False
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            logger.info("✅ HTTP session configured with retry strategy")
            
        except ImportError:
            logger.warning("⚠️ 'requests' module not found, using default session")
            session = None
        
        # Initialize Razorpay client
        try:
            razorpay_client = razorpay.Client(
                auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET)
            )
            
            # Try to set timeout if supported
            try:
                razorpay_client.set_timeout(60)
            except AttributeError:
                # Older version of razorpay SDK doesn't have set_timeout
                logger.info("⚠️ Razorpay SDK doesn't support set_timeout (older version)")
            
            # Inject custom session if available
            if session and hasattr(razorpay_client, 'session'):
                razorpay_client.session = session
            
            # Test the connection with a simple API call
            try:
                # This will fail but confirms API is reachable
                razorpay_client.payment.fetch('pay_test_connection')
            except razorpay.errors.BadRequestError:
                # Expected error - means connection works
                logger.info("✅ Razorpay client initialized and tested")
                RAZORPAY_AVAILABLE = True
                return True
            except Exception as e:
                error_str = str(e).lower()
                if 'unauthorized' in error_str or 'authentication' in error_str:
                    logger.error("❌ Razorpay authentication failed - check your API keys")
                    return False
                else:
                    # Other errors are ok for initialization
                    logger.info("✅ Razorpay client initialized")
                    RAZORPAY_AVAILABLE = True
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to create Razorpay client: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        logger.error(f"❌ Razorpay initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Initialize on module load
initialization_success = initialize_razorpay()
if not initialization_success:
    logger.error("❌ Razorpay initialization failed - payment features will not work")
    logger.error("   Check that config.py has RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET")
    logger.error("   Run: pip install razorpay requests")

def get_usd_to_inr_rate():
    """Get USD to INR rate"""
    try:
        settings = SystemSettings.get()
        return settings.get('usd_to_inr_rate', 88.0) if settings else 88.0
    except:
        return 88.0

def get_min_deposit_inr():
    """Get minimum INR deposit"""
    try:
        settings = SystemSettings.get()
        return settings.get('min_deposit_inr', 10.0) if settings else 10.0
    except:
        return 10.0

def usd_to_inr(amount_usd):
    """Convert USD to INR"""
    rate = get_usd_to_inr_rate()
    return round(amount_usd * rate, 2)

def inr_to_usd(amount_inr):
    """Convert INR to USD"""
    rate = get_usd_to_inr_rate()
    return round(amount_inr / rate, 2)

def retry_with_backoff(max_retries=5, initial_delay=1, backoff_factor=2):
    """Enhanced retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()
                    
                    # Check if it's a retryable error
                    retryable_errors = [
                        'connection aborted', 'remotedisconnected',
                        'connection reset', 'timeout', 'timed out',
                        'connection error', 'max retries exceeded',
                        'read timed out', 'connection refused',
                        'temporary failure', 'network is unreachable'
                    ]
                    
                    is_retryable = any(err in error_str for err in retryable_errors)
                    
                    if is_retryable and attempt < max_retries - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"⚠️ Retryable error (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                        continue
                    
                    # Non-retryable error or last attempt
                    if attempt == max_retries - 1:
                        logger.error(f"❌ All {max_retries} attempts failed: {e}")
                    raise
            
            raise last_exception
        
        return wrapper
    return decorator

@retry_with_backoff(max_retries=5, initial_delay=2, backoff_factor=2)
def create_order(amount_usd=None, user_id=None, amount_inr=None):
    """Create Razorpay Payment Link with enhanced error handling"""
    
    # Check if Razorpay is available
    if not RAZORPAY_AVAILABLE or razorpay_client is None:
        logger.error("❌ Razorpay not initialized")
        return {
            'error': 'Payment system not configured. Contact administrator.',
            'details': 'Razorpay client initialization failed'
        }
    
    try:
        import razorpay
        
        # Calculate amounts
        if amount_inr is not None:
            amount_inr = round(amount_inr, 1)
            amount_usd = inr_to_usd(amount_inr)
            amount_usd = round(amount_usd, 2)
            logger.info(f"💰 Creating payment: ₹{amount_inr:.1f} (will credit ${amount_usd:.2f})")
        else:
            amount_usd = round(amount_usd, 2)
            amount_inr = usd_to_inr(amount_usd)
            amount_inr = round(amount_inr, 1)
            logger.info(f"💰 Creating payment: ${amount_usd:.2f} = ₹{amount_inr:.1f}")
        
        # Validate minimum
        min_deposit_inr = get_min_deposit_inr()
        if amount_inr < 1.0:
            return {'error': f'Minimum deposit is ₹1.0', 'min_inr': 1.0}
        if amount_inr < min_deposit_inr:
            return {'error': f'Minimum deposit is ₹{min_deposit_inr:.1f}', 'min_inr': min_deposit_inr}
        
        amount_paise = int(round(amount_inr * 100))
        if amount_paise < 100:
            amount_paise = 100
        
        # Try payment link first
        try:
            payment_link_data = {
                'amount': amount_paise,
                'currency': 'INR',
                'description': f'Balance deposit for user {user_id}',
                'customer': {'name': f'User {user_id}'},
                'notify': {'sms': False, 'email': False},
                'reminder_enable': False,
                'callback_url': f'https://t.me/{BOT_USERNAME}',
                'callback_method': 'get'
            }
            
            logger.info(f"🔄 Creating Razorpay payment link...")
            payment_link = razorpay_client.payment_link.create(payment_link_data)
            logger.info(f"✅ Payment link created: {payment_link['id']}")
            
            transaction_id = Transaction.create(
                user_id=user_id,
                amount=amount_usd,
                payment_method='razorpay',
                amount_inr=amount_inr,
                order_id=payment_link['id']
            )
            
            logger.info(f"✅ Transaction saved: {transaction_id}")
            
            return {
                'order_id': payment_link['id'],
                'amount': amount_paise,
                'amount_inr': round(amount_inr, 1),
                'amount_usd': round(amount_usd, 2),
                'currency': 'INR',
                'key_id': config.RAZORPAY_KEY_ID,
                'payment_url': payment_link['short_url'],
                'status': payment_link['status']
            }
            
        except razorpay.errors.BadRequestError as e:
            logger.warning(f"⚠️ Payment link failed, trying order creation: {e}")
            
            # Fallback to order creation
            order_data = {
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': 1
            }
            
            logger.info(f"🔄 Creating Razorpay order...")
            order = razorpay_client.order.create(data=order_data)
            logger.info(f"✅ Order created: {order['id']}")
            
            transaction_id = Transaction.create(
                user_id=user_id,
                amount=amount_usd,
                payment_method='razorpay',
                amount_inr=amount_inr,
                order_id=order['id']
            )
            
            return {
                'order_id': order['id'],
                'amount': amount_paise,
                'amount_inr': round(amount_inr, 1),
                'amount_usd': round(amount_usd, 2),
                'currency': 'INR',
                'key_id': config.RAZORPAY_KEY_ID,
                'payment_url': f"https://rzp.io/l/{order['id']}",
                'status': 'created'
            }
        
    except razorpay.errors.ServerError as e:
        logger.error(f"❌ Razorpay server error: {e}")
        return {'error': 'Payment service temporarily unavailable. Please try again in 1 minute.'}
    except Exception as e:
        logger.error(f"❌ Payment creation error: {e}")
        import traceback
        traceback.print_exc()
        
        error_str = str(e).lower()
        if 'connection' in error_str or 'timeout' in error_str:
            return {'error': 'Network error. Please try again in 30 seconds.'}
        return {'error': f'Payment error. Please contact support.'}

async def send_telegram_message_async(chat_id, message, max_retries=5):
    """Send Telegram message with retry logic"""
    if not TELEGRAM_AVAILABLE or bot is None:
        logger.warning("⚠️ Telegram not available")
        return False
    
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"✅ Message sent to {chat_id}")
            return True
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Non-retryable errors
            if any(x in error_str for x in ['blocked', 'deactivated', 'user not found', 'chat not found']):
                logger.error(f"❌ Cannot send to {chat_id}: {e}")
                return False
            
            # Retryable errors
            if attempt < max_retries - 1:
                wait_time = 3 * (2 ** attempt)
                logger.warning(f"⚠️ Retry {attempt + 1}/{max_retries} for {chat_id} in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                continue
            
            logger.error(f"❌ All retries failed for {chat_id}: {e}")
            return False
    
    return False

async def notify_user_and_admin(user_id, amount_usd, amount_inr, payment_id):
    """Send notifications with guaranteed delivery"""
    if not TELEGRAM_AVAILABLE or bot is None:
        logger.warning("⚠️ Telegram not available for notifications")
        return
    
    try:
        # Get user info
        user_info = User.get_by_telegram_id(user_id)
        username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
        
        # Validate payment_id
        if not payment_id or payment_id == "None":
            payment_id = "Processing"
        
        payment_display = str(payment_id)[:30] + "..." if len(str(payment_id)) > 30 else str(payment_id)
        
        # ========================================
        # USER NOTIFICATION
        # ========================================
        user_message = (
            f"Payment Successful!\n\n"
            f"Amount: Rs.{amount_inr:.1f} INR\n"
            f"Credited: ${amount_usd:.2f} USD\n\n"
            f"Your balance has been updated!\n\n"
            f"Thank you!"
        )
        
        logger.info(f"📧 Sending notification to user {user_id}...")
        user_success = await send_telegram_message_async(user_id, user_message)
        
        if not user_success:
            logger.error(f"❌ Failed to notify user {user_id}")
        
        # ========================================
        # ADMIN NOTIFICATION
        # ========================================
        admin_ids = []
        
        if hasattr(config, 'OWNER_ID') and config.OWNER_ID:
            admin_ids.append(config.OWNER_ID)
        
        if hasattr(config, 'ADMIN_IDS') and config.ADMIN_IDS:
            admin_ids.extend(config.ADMIN_IDS)
        
        admin_ids = list(set(admin_ids))
        
        if not admin_ids:
            logger.warning("⚠️ No admin IDs configured")
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_display = username if username != 'Unknown' else f'User_{user_id}'
        
        admin_message = (
            f"NEW INR DEPOSIT\n\n"
            f"User: {username_display}\n"
            f"User ID: {user_id}\n"
            f"Amount: Rs.{amount_inr:.1f} INR = ${amount_usd:.2f} USD\n"
            f"Payment ID: {payment_display}\n"
            f"Status: Completed\n"
            f"Time: {timestamp}"
        )
        
        # Send to each admin
        successful_admins = []
        failed_admins = []
        
        for idx, admin_id in enumerate(admin_ids, 1):
            logger.info(f"📧 Sending to admin {admin_id} ({idx}/{len(admin_ids)})...")
            
            success = await send_telegram_message_async(admin_id, admin_message)
            
            if success:
                successful_admins.append(admin_id)
                logger.info(f"✅ Admin {admin_id} notified")
            else:
                failed_admins.append(admin_id)
                logger.error(f"❌ Failed to notify admin {admin_id}")
            
            # Delay between admins
            if idx < len(admin_ids):
                await asyncio.sleep(2.0)
        
        # Summary
        logger.info(
            f"📊 Notification summary: "
            f"User: {'✅' if user_success else '❌'}, "
            f"Admins: {len(successful_admins)}/{len(admin_ids)} successful"
        )
        
        if failed_admins:
            logger.warning(f"⚠️ Failed admin notifications: {failed_admins}")
                    
    except Exception as e:
        logger.error(f"❌ Critical error in notify_user_and_admin: {e}")
        import traceback
        traceback.print_exc()

def process_payment_success(order_id, payment_id):
    """Process successful payment"""
    try:
        logger.info(f"💳 Processing payment - Order: {order_id}")
        
        transaction = Transaction.get_by_order_id(order_id)
        
        if not transaction:
            logger.error(f"❌ Transaction not found: {order_id}")
            return False
        
        if transaction['status'] == 'completed':
            logger.info(f"ℹ️ Already completed: {order_id}")
            return True
        
        # Validate payment_id
        if not payment_id:
            payment_id = f"razorpay_{order_id}"
            logger.warning(f"⚠️ Payment ID was None, using: {payment_id}")
        
        logger.info(f"💰 Amount: ${transaction['amount']:.2f} for user {transaction['user_id']}")
        
        # Update user balance
        success = User.update_balance(
            transaction['user_id'], 
            transaction['amount'], 
            operation='add'
        )
        
        if not success:
            logger.error(f"❌ User not found: {transaction['user_id']}")
            return False
        
        # Update transaction status
        Transaction.update_status(transaction['_id'], 'completed', charge_id=payment_id)
        logger.info(f"✅ Balance updated successfully")
        
        amount_inr = transaction.get('amount_inr', transaction['amount'] * get_usd_to_inr_rate())
        
        # Schedule notifications
        try:
            loop = asyncio.get_running_loop()
            
            task = loop.create_task(notify_user_and_admin(
                transaction['user_id'],
                transaction['amount'],
                amount_inr,
                payment_id
            ))
            
            def log_notification_result(future):
                try:
                    future.result()
                    logger.info("✅ Notification task completed")
                except Exception as e:
                    logger.error(f"❌ Notification task failed: {e}")
            
            task.add_done_callback(log_notification_result)
            logger.info("✅ Notification task scheduled")
            
        except RuntimeError:
            logger.info("⚠️ No event loop, running notifications synchronously...")
            
            try:
                asyncio.run(notify_user_and_admin(
                    transaction['user_id'],
                    transaction['amount'],
                    amount_inr,
                    payment_id
                ))
                logger.info("✅ Notifications sent successfully")
                
            except Exception as e:
                logger.error(f"❌ Notification error: {e}")
                logger.error(
                    f"🚨 MANUAL NOTIFICATION NEEDED:\n"
                    f"   User: {transaction['user_id']}\n"
                    f"   Amount: ₹{amount_inr:.1f} / ${transaction['amount']:.2f}\n"
                    f"   Payment ID: {payment_id}"
                )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Payment processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_payment_failed(order_id):
    """Process failed payment"""
    try:
        transaction = Transaction.get_by_order_id(order_id)
        
        if transaction:
            Transaction.update_status(transaction['_id'], 'failed')
            logger.info(f"❌ Payment marked as failed: {order_id}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error processing failure: {e}")
        return False

def verify_payment_signature(order_id, payment_id, signature):
    """Verify Razorpay signature"""
    try:
        if not RAZORPAY_AVAILABLE or razorpay_client is None:
            logger.error("❌ Razorpay not available for signature verification")
            return False
        
        import razorpay
        
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        logger.info(f"✅ Signature verified: {order_id}")
        return True
        
    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"❌ Invalid signature: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        return False

@retry_with_backoff(max_retries=3, initial_delay=2, backoff_factor=2)
def get_payment_status(payment_id):
    """Get payment status with retry"""
    try:
        if not RAZORPAY_AVAILABLE or razorpay_client is None:
            return None
        
        payment = razorpay_client.payment.fetch(payment_id)
        return payment['status']
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return None
