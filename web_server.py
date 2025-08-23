from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from classify import ImageClassifier
import os
from functools import wraps
from datetime import datetime, timezone
import hashlib
import hmac
import time
import base64
import logging
from services.discord import init_discord_logging, get_discord_handler

app = Flask(__name__)

# Configure Flask request logging
class RequestLogger:
    def __init__(self, app):
        self.app = app
        self.discord_handler = None
        
    def init_app(self, discord_handler):
        self.discord_handler = discord_handler
        
        @self.app.before_request
        def before_request():
            request.start_time = time.time()
            
        @self.app.after_request
        def after_request(response):
            if self.discord_handler and request.path in ['/classify', '/api/classify']:
                # Calculate request processing time
                request_time = time.time() - getattr(request, 'start_time', time.time())
                
                # Format log like: 127.0.0.1 - - [22/Aug/2025 16:49:08] "POST /classify HTTP/1.1" 200 -
                timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
                log_line = f'{request.remote_addr} - - [{timestamp}] "{request.method} {request.path} {request.environ.get("SERVER_PROTOCOL", "HTTP/1.1")}" {response.status_code} - ({request_time:.3f}s)'
                
                # Send this log to Discord immediately
                self.discord_handler.info(f"HTTP Request: {log_line}")
                self.discord_handler.flush()
                
            return response

request_logger = RequestLogger(app)
app.secret_key = 'your-secret-key-change-in-production'

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Discord logging
discord_logger = init_discord_logging()

# Initialize request logger
request_logger.init_app(discord_logger)

# Set up Flask logger to use Discord
class DiscordLogHandler(logging.Handler):
    def __init__(self, discord_logger):
        super().__init__()
        self.discord_logger = discord_logger
        
    def emit(self, record):
        log_entry = self.format(record)
        if record.levelno >= logging.ERROR:
            self.discord_logger.error(f"Flask: {log_entry}")
            self.discord_logger.flush()  # Immediately send error logs
        elif record.levelno >= logging.WARNING:
            self.discord_logger.warning(f"Flask: {log_entry}")
        else:
            self.discord_logger.info(f"Flask: {log_entry}")

# Configure Flask logger
flask_logger = logging.getLogger('werkzeug')
discord_handler = DiscordLogHandler(discord_logger)
discord_handler.setLevel(logging.INFO)
discord_handler.setFormatter(logging.Formatter('%(message)s'))
flask_logger.addHandler(discord_handler)

# Enable CORS for all routes by default
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,X-API-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Handle preflight OPTIONS requests for all routes
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options_wildcard(path=None):
    response = jsonify({'status': 'preflight'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,X-API-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Handle preflight OPTIONS requests for root
@app.route('/', methods=['OPTIONS'])
def handle_options_root():
    response = jsonify({'status': 'preflight'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,X-API-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Load classifier on startup
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "pt", "model_weights.pth")
encoder_path = os.path.join(base_dir, "pt", "label_encoder.pth")

try:
    classifier = ImageClassifier(model_path, encoder_path, use_mapping=True)
    print("Classifier loaded successfully")
    discord_logger.info("Classifier loaded successfully")
except Exception as e:
    error_msg = f"Error loading classifier: {e}"
    print(error_msg)
    discord_logger.error(error_msg)
    classifier = None

# Load API key from .env file or use default
try:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv('API_KEY', 'default_api_key')
    print(f"Loaded API key from .env file")
    discord_logger.info("Loaded API key from .env file")
except ImportError:
    # Fallback if python-dotenv is not installed
    API_KEY = os.environ.get('API_KEY', 'default_api_key')
    print("Using environment variable for API key")
    discord_logger.warning("python-dotenv not installed, using environment variable for API key")

# Request statistics
stats = {
    'requests_total': 0,
    'requests_successful': 0,
    'requests_failed': 0,
    'start_time': datetime.now().isoformat()
}

# Header name
API_KEY_HEADER = 'X-API-Key'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        
        global stats
        stats['requests_total'] += 1
        
        api_key = request.headers.get(API_KEY_HEADER)
        client_ip = request.remote_addr
        endpoint = request.path
        
        if not api_key:
            stats['requests_failed'] += 1
            discord_logger.warning(f"API request failed: Missing API key header | IP: {client_ip} | Endpoint: {endpoint}")
            return jsonify({'error': 'Missing API key header'}), 401
        
        # Verify API key
        if api_key != API_KEY:
            stats['requests_failed'] += 1
            discord_logger.warning(f"API request failed: Invalid API key | IP: {client_ip} | Endpoint: {endpoint}")
            return jsonify({'error': 'Invalid API key'}), 401
            
        stats['requests_successful'] += 1
        return f(*args, **kwargs)
    return decorated

# ============ WEB UI ROUTES ============

@app.route('/')
def index():
    """Main web UI for image classification"""
    return render_template('index.html', 
                         api_key=API_KEY,
                         classifier_loaded=classifier is not None)

@app.route('/classify', methods=['POST'])
def web_classify():
    """Web form classification endpoint"""
    # Immediately log the request and flush logs
    client_ip = request.remote_addr
    discord_logger.info(f"WEB UI classification request received | IP: {client_ip}")
    discord_logger.flush()  # Immediately send logs
    
    if 'image' not in request.files:
        discord_logger.warning(f"WEB UI classification failed: No image provided | IP: {client_ip}")
        discord_logger.flush()  # Immediately send logs
        flash('No image file provided', 'error')
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '':
        discord_logger.warning(f"WEB UI classification failed: Empty filename | IP: {client_ip}")
        discord_logger.flush()  # Immediately send logs
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        discord_logger.warning(f"WEB UI classification failed: Invalid file type | File: {file.filename} | IP: {client_ip}")
        discord_logger.flush()  # Immediately send logs
        flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF files.', 'error')
        return redirect(url_for('index'))
    
    if not classifier:
        discord_logger.error(f"WEB UI classification failed: Classifier not loaded | IP: {client_ip}")
        discord_logger.flush()  # Immediately send logs
        flash('Classifier not loaded. Please check server configuration.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Classify the image
        class_name, confidence, original_class = classifier.predict_single_image(filepath)
        
        # Convert image to base64 for display
        with open(filepath, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
            img_src = f"data:image/{filename.split('.')[-1]};base64,{img_data}"
        
        # Clean up
        os.remove(filepath)
        
        # Log successful classification and flush
        discord_logger.info(f"WEB UI classification successful | File: {filename} | Class: {class_name} | Confidence: {confidence:.2f} | IP: {request.remote_addr}")
        discord_logger.flush()  # Immediately send logs
        
        # Render results
        return render_template('results.html',
                             class_name=class_name,
                             confidence=confidence,
                             original_class=original_class,
                             image_src=img_src,
                             filename=filename)
        
    except Exception as e:
        error_msg = f'Error processing image: {str(e)}'
        discord_logger.error(f"Web UI classification error: {error_msg} | File: {filename}")
        discord_logger.flush()  # Immediately send logs
        flash(error_msg, 'error')
        return redirect(url_for('index'))

@app.route('/api-test')
def api_test():
    """API testing interface"""
    return render_template('api_test.html',
                         api_key=API_KEY)

# ============ API ROUTES ============

@app.route('/api/classify', methods=['POST', 'OPTIONS'])
@require_api_key
def classify_image():
    """
    API endpoint for image classification
    Expects: multipart/form-data with an 'image' file
    Returns: JSON with classification results
    """
    # Immediately log the API request
    client_ip = request.remote_addr
    request_method = request.method
    
    if request_method == 'POST':
        discord_logger.info(f"API classification request received | IP: {client_ip} | POST /api/classify")
        discord_logger.flush()  # Immediately send logs
    
    if request_method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-API-Key,X-API-Signature,X-API-Timestamp'
        response.headers['Access-Control-Allow-Methods'] = 'POST,OPTIONS'
        return response
    
    if not classifier:
        discord_logger.error(f"API classification failed: Classifier not loaded | IP: {client_ip}")
        discord_logger.flush()  # Immediately send logs
        response = jsonify({'error': 'Classifier not loaded'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500
        
    if 'image' not in request.files:
        discord_logger.warning(f"API classification failed: No image provided | IP: {client_ip}")
        discord_logger.flush()  # Immediately send logs
        response = jsonify({'error': 'No image file provided'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 400
        
    file = request.files['image']
    if file.filename == '':
        discord_logger.warning(f"API classification failed: Empty filename | IP: {client_ip}")
        discord_logger.flush()  # Immediately send logs
        response = jsonify({'error': 'No selected file'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 400
        
    try:
        # Create temporary file path
        temp_path = os.path.join(os.path.dirname(__file__), 'temp_uploads', file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        # Save and process the file
        file.save(temp_path)
        class_name, confidence, original_class = classifier.predict_single_image(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        # Log successful classification and flush immediately
        discord_logger.info(f"API classification successful | File: {file.filename} | Class: {class_name} | Confidence: {float(confidence):.2f} | IP: {request.remote_addr}")
        discord_logger.flush()  # Immediately send logs
        
        # Return results
        response = jsonify({
            'success': True,
            'class_name': class_name,
            'confidence': float(confidence),
            'original_class': original_class,
            'timestamp': datetime.now().isoformat()
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        error_msg = str(e)
        discord_logger.error(f"API classification error: {error_msg} | File: {file.filename} | IP: {request.remote_addr}")
        discord_logger.flush()  # Immediately send logs
        response = jsonify({'success': False, 'error': error_msg})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint - no authentication required"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-API-Key,X-API-Signature,X-API-Timestamp'
        response.headers['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        return response
    
    response = jsonify({
        'status': 'healthy',
        'classifier_loaded': classifier is not None,
        'timestamp': datetime.now().isoformat()
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/test-cors', methods=['GET', 'OPTIONS'])
def test_cors():
    """Simple endpoint to test CORS functionality"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        return response
    
    response = jsonify({
        'message': 'CORS is working!',
        'timestamp': datetime.now().isoformat(),
        'method': request.method
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Get API usage statistics"""
    uptime_seconds = (datetime.now() - datetime.fromisoformat(stats['start_time'])).total_seconds()
    
    return jsonify({
        'status': 'running',
        'uptime_seconds': int(uptime_seconds),
        'uptime_human': format_uptime(uptime_seconds),
        'requests_total': stats['requests_total'],
        'requests_successful': stats['requests_successful'],
        'requests_failed': stats['requests_failed'],
        'success_rate': (stats['requests_successful'] / max(stats['requests_total'], 1)) * 100,
        'timestamp': datetime.now().isoformat()
    })

def format_uptime(seconds):
    """Format uptime in human readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Image Classification Web Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    start_msg = f"Starting web server on {args.host}:{args.port}"
    print(start_msg)
    discord_logger.info(start_msg)
    print(f"API Key: {API_KEY}")
    print(f"Classifier loaded: {classifier is not None}")
    discord_logger.info(f"Classifier loaded: {classifier is not None}")
    print(f"Web UI: http://{args.host}:{args.port}")
    print(f"API Test: http://{args.host}:{args.port}/api-test")
    discord_logger.info(f"Web UI available at: http://{args.host}:{args.port}")
    
    try:
        # Register graceful shutdown handlers
        import signal
        import sys
        
        def signal_handler(sig, frame):
            print(f"Received signal {sig}, shutting down gracefully...")
            discord_logger.info(f"Received signal {sig}, shutting down gracefully...")
            from services.discord import log_service_shutdown
            log_service_shutdown(f"Received signal {sig}")
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start Flask application
        app.run(
            host=args.host, 
            port=args.port, 
            debug=args.debug,
            threaded=True
        )
    except Exception as e:
        error_msg = f"Error starting server: {str(e)}"
        print(error_msg)
        discord_logger.critical(error_msg)
