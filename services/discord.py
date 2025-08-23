import requests
import json
import logging
import time
import threading
import os
import sys
import traceback
import queue
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Configure logging
logger = logging.getLogger("discord_logger")
logger.setLevel(logging.INFO)

# Create a custom formatter for logs
class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        return f"[{log_time}] [{record.levelname}] {record.getMessage()}"

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)

# Create file handler for logs
os.makedirs('logs', exist_ok=True)
file_handler = logging.FileHandler('logs/discord.log')
file_handler.setFormatter(CustomFormatter())
logger.addHandler(file_handler)

class DiscordWebhookHandler:
    def __init__(self, webhook_url, interval=15):
        self.webhook_url = webhook_url
        self.interval = interval
        self.log_queue = queue.Queue()
        self.running = False
        self.thread = None
        
        # Add signal handlers for graceful shutdown
        try:
            import signal
            signal.signal(signal.SIGINT, self.handle_signal)
            signal.signal(signal.SIGTERM, self.handle_signal)
        except (ImportError, AttributeError):
            logger.warning("Signal handling not supported on this platform")
    
    def handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}. Shutting down Discord webhook handler...")
        self.stop()
        # Send final shutdown message
        self.send_message("**Service Shutdown**: API service is shutting down.")
    
    def add_log(self, level, message):
        """Add a log message to the queue"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.log_queue.put(log_entry)
    
    def info(self, message):
        """Log an info message"""
        logger.info(message)
        self.add_log("INFO", message)
    
    def warning(self, message):
        """Log a warning message"""
        logger.warning(message)
        self.add_log("WARNING", message)
    
    def error(self, message):
        """Log an error message"""
        logger.error(message)
        self.add_log("ERROR", message)
    
    def critical(self, message):
        """Log a critical message"""
        logger.critical(message)
        self.add_log("CRITICAL", message)
        # Critical errors are sent immediately
        self.send_message(f"**CRITICAL ERROR**: {message}")
    
    def exception(self, message):
        """Log an exception with traceback"""
        exception_details = traceback.format_exc()
        logger.exception(message)
        self.add_log("ERROR", f"{message}\n```{exception_details}```")
    
    def start(self):
        """Start the webhook sender thread"""
        if self.running and self.thread and self.thread.is_alive():
            logger.info("Discord webhook handler is already running")
            return
        
        if not self.webhook_url:
            logger.error("Discord webhook URL is not configured. Logs will not be sent to Discord.")
            return
        
        # Reset state in case thread died
        self.running = False
        if self.thread:
            try:
                self.thread.join(timeout=1)
            except:
                pass
        
        # Start fresh thread
        self.running = True
        self.thread = threading.Thread(target=self._sender_thread, daemon=True, name="DiscordLoggerThread")
        self.thread.start()
        
        # Verify thread started successfully
        if not self.thread.is_alive():
            logger.error("Failed to start Discord webhook thread")
            self.running = False
            return
            
        logger.info(f"Discord webhook handler started with {self.interval} second interval")
        
        # Send a test message to verify connectivity
        try:
            self.send_message(f"**Discord Logger Started**: Logging interval set to {self.interval} seconds")
        except Exception as e:
            logger.error(f"Failed to send initial message to Discord: {str(e)}")
    
    def flush(self):
        """Force send all logs in the queue immediately"""
        if not self.running or not self.webhook_url:
            return
            
        try:
            # Collect all logs from the queue
            logs = []
            try:
                while not self.log_queue.empty():
                    logs.append(self.log_queue.get_nowait())
                    self.log_queue.task_done()
            except queue.Empty:
                pass
            
            # If there are logs, send them to Discord
            if logs:
                content = "**Log Update (Forced Flush)**\n"
                for log in logs:
                    content += f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                
                # Ensure the message is not too long for Discord
                if len(content) > 1900:
                    content = content[:1900] + "...\n(Message truncated due to length)"
                
                self.send_message(content)
                return True
        except Exception as e:
            logger.error(f"Error flushing logs: {str(e)}")
        
        return False

    def stop(self):
        """Stop the webhook sender thread"""
        # Flush any remaining logs
        self.flush()
        
        self.running = False
        if self.thread:
            try:
                self.thread.join(timeout=10)
            except Exception as e:
                logger.error(f"Error stopping thread: {str(e)}")
        
        logger.info("Discord webhook handler stopped")
    
    def _sender_thread(self):
        """Thread that periodically sends logs to Discord"""
        last_heartbeat_time = time.time()
        last_sent_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                time_since_last_send = current_time - last_sent_time
                
                # Collect all logs from the queue
                logs = []
                try:
                    while not self.log_queue.empty():
                        logs.append(self.log_queue.get_nowait())
                        self.log_queue.task_done()
                except queue.Empty:
                    pass
                
                # Send logs if we have any or if it's time for a heartbeat check
                send_update = False
                content = "**Log Update**\n"
                
                if logs:
                    for log in logs:
                        content += f"[{log['timestamp']}] [{log['level']}] {log['message']}\n"
                    send_update = True
                    
                # Send a heartbeat message every 5 minutes even if no logs
                if current_time - last_heartbeat_time > 300:  # 5 minutes
                    if not logs:  # Only add heartbeat if we don't already have logs
                        content += f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Service heartbeat - still running\n"
                    last_heartbeat_time = current_time
                    send_update = True
                
                # Force send if it's been too long since the last update (2x interval as buffer)
                if time_since_last_send >= (self.interval * 2):
                    if not send_update:  # If we're not already sending something
                        content += f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Periodic log update - no new messages\n"
                        send_update = True
                
                if send_update:
                    # Ensure the message is not too long for Discord
                    if len(content) > 1900:
                        content = content[:1900] + "...\n(Message truncated due to length)"
                    
                    self.send_message(content)
                    last_sent_time = current_time
            
            except Exception as e:
                logger.error(f"Error in webhook sender thread: {str(e)}")
                # Try to report the error to Discord
                try:
                    error_msg = f"**ERROR**: Discord logger thread encountered an error: {str(e)}"
                    self.send_message(error_msg)
                except:
                    pass
            
            # Sleep for a shorter interval and check more frequently
            # This makes the timer more accurate
            time.sleep(min(5, self.interval))
    
    def send_message(self, content):
        """Send a message to Discord webhook"""
        if not self.webhook_url:
            return
        
        try:
            data = {
                "content": content,
                "username": "Image Classification API"
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 204:
                logger.error(f"Failed to send message to Discord. Status code: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error sending message to Discord: {str(e)}")


# Create a global instance of the Discord webhook handler
discord_handler = None

def get_system_info():
    """Get system information for logging"""
    import platform
    import socket
    import psutil
    import torch
    
    try:
        # Basic system information
        sys_info = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory_total": f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB",
            "memory_available": f"{psutil.virtual_memory().available / (1024 ** 3):.2f} GB",
            "disk_total": f"{psutil.disk_usage('/').total / (1024 ** 3):.2f} GB",
            "disk_free": f"{psutil.disk_usage('/').free / (1024 ** 3):.2f} GB"
        }
        
        # Add PyTorch information if available
        sys_info["torch_version"] = torch.__version__
        sys_info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            sys_info["cuda_device"] = torch.cuda.get_device_name(0)
            sys_info["cuda_version"] = torch.version.cuda
            
        return sys_info
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {"error": str(e)}

def format_system_info(sys_info):
    """Format system information for Discord message"""
    message = "**System Information:**\n"
    message += f"🖥️ **Host**: {sys_info.get('hostname', 'Unknown')}\n"
    message += f"⚙️ **OS**: {sys_info.get('platform', 'Unknown')}\n"
    message += f"🐍 **Python**: {sys_info.get('python_version', 'Unknown')}\n"
    message += f"🧠 **CPU**: {sys_info.get('processor', 'Unknown')} ({sys_info.get('cpu_count', 'Unknown')} cores)\n"
    message += f"💾 **Memory**: {sys_info.get('memory_available', 'Unknown')} available of {sys_info.get('memory_total', 'Unknown')}\n"
    message += f"💿 **Disk**: {sys_info.get('disk_free', 'Unknown')} free of {sys_info.get('disk_total', 'Unknown')}\n"
    
    # Add PyTorch information if available
    if "torch_version" in sys_info:
        message += f"\n🔥 **PyTorch**: {sys_info.get('torch_version', 'Unknown')}\n"
        message += f"🚀 **CUDA Available**: {sys_info.get('cuda_available', False)}\n"
        if sys_info.get('cuda_available', False):
            message += f"📊 **CUDA Device**: {sys_info.get('cuda_device', 'Unknown')}\n"
            message += f"📋 **CUDA Version**: {sys_info.get('cuda_version', 'Unknown')}\n"
    
    return message

# Discord logger watchdog
def _discord_logger_watchdog():
    """Watchdog thread to ensure Discord logger stays alive"""
    global discord_handler
    while True:
        try:
            # Check if handler exists and is running
            if discord_handler and not (discord_handler.thread and discord_handler.thread.is_alive()):
                logger.warning("Discord logger thread died, restarting...")
                discord_handler.start()
        except Exception as e:
            logger.error(f"Error in Discord logger watchdog: {str(e)}")
        
        # Check every 30 seconds
        time.sleep(30)

def init_discord_logging():
    """Initialize the Discord webhook handler"""
    global discord_handler
    if discord_handler is None:
        # Create the handler
        discord_handler = DiscordWebhookHandler(DISCORD_WEBHOOK_URL)
        discord_handler.start()
        
        # Start the watchdog thread to ensure logger stays alive
        watchdog_thread = threading.Thread(
            target=_discord_logger_watchdog, 
            daemon=True,
            name="DiscordLoggerWatchdog"
        )
        watchdog_thread.start()
        
        try:
            # Get system information
            sys_info = get_system_info()
            system_info_msg = format_system_info(sys_info)
            
            # Send startup message with system info
            startup_msg = "**🟢 Service Started**: Image Classification API service is now running.\n\n"
            startup_msg += system_info_msg
            discord_handler.send_message(startup_msg)
        except Exception as e:
            logger.error(f"Error sending startup info: {str(e)}")
            # Fallback to simple message if system info fails
            discord_handler.send_message("**🟢 Service Started**: Image Classification API service is now running.")
    elif not discord_handler.running or not (discord_handler.thread and discord_handler.thread.is_alive()):
        # Restart if handler exists but thread is not running
        discord_handler.start()
    
    return discord_handler

def get_discord_handler():
    """Get the Discord webhook handler instance"""
    global discord_handler
    if discord_handler is None:
        return init_discord_logging()
    return discord_handler

# Function to log service shutdown
def log_service_shutdown(reason="Normal shutdown"):
    """Log service shutdown"""
    try:
        handler = get_discord_handler()
        if not handler:
            logger.error("Cannot log shutdown: Discord handler not initialized")
            return
            
        handler.info(f"Service shutdown: {reason}")
        
        # Force flush logs first
        handler.flush()
        
        # Send a more visible shutdown message to Discord
        try:
            uptime = "Unknown"
            try:
                import psutil
                from datetime import datetime, timedelta
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = str(timedelta(seconds=(datetime.now() - boot_time).total_seconds()))
            except Exception as e:
                logger.error(f"Error getting uptime: {str(e)}")
                pass
            
            shutdown_msg = f"**🔴 Service Shutdown**: Image Classification API service is shutting down.\n"
            shutdown_msg += f"📝 **Reason**: {reason}\n"
            shutdown_msg += f"⏱️ **Uptime**: {uptime}\n"
            shutdown_msg += f"🕒 **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Use direct send to ensure delivery
            handler.send_message(shutdown_msg)
            
            # Small delay to ensure message is sent
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error sending shutdown message: {str(e)}")
        
        # Now stop the handler
        handler.stop()
    except Exception as e:
        logger.critical(f"Critical error during shutdown logging: {str(e)}")
        # Try one last direct message
        try:
            requests.post(
                DISCORD_WEBHOOK_URL,
                data=json.dumps({
                    "content": f"**🔴 EMERGENCY SHUTDOWN**: Service crashed during shutdown. Reason: {reason}",
                    "username": "Image Classification API"
                }),
                headers={"Content-Type": "application/json"}
            )
        except:
            pass
    
# Register a shutdown handler with atexit
import atexit
atexit.register(log_service_shutdown)

# If this module is run directly, test the webhook
if __name__ == "__main__":
    handler = init_discord_logging()
    handler.info("Test message from Discord webhook handler")
    handler.warning("This is a test warning")
    handler.error("This is a test error")
    time.sleep(10)  # Wait for messages to be sent
    handler.stop()
