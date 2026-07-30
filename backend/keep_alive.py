"""
Keep-alive service for Render deployment
Pings the backend every 5 minutes to prevent spin-down
"""

import requests
import time
import logging
import sys
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger("keep_alive")

# Default Render backend URL
RENDER_BACKEND_URL = "https://physioverse-backend.onrender.com"
PING_INTERVAL = 300  # 5 minutes in seconds


class KeepAliveService:
    """Keep-alive service for Render backend"""
    
    def __init__(self, backend_url: str, interval: int = 300):
        self.backend_url = backend_url.rstrip("/")
        self.health_endpoint = f"{self.backend_url}/health"
        self.interval = interval
        self.scheduler = BackgroundScheduler()
        self.ping_count = 0
        self.last_ping_time = None
        self.last_status_code = None
        
    def ping_backend(self):
        """Send health check ping to backend"""
        try:
            self.ping_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"🔔 Ping #{self.ping_count} → {self.health_endpoint}")
            
            response = requests.get(
                self.health_endpoint,
                timeout=10
            )
            
            self.last_status_code = response.status_code
            self.last_ping_time = timestamp
            
            if response.status_code == 200:
                logger.info(f"✅ Success (200 OK) - Response: {response.json()}")
            else:
                logger.warning(f"⚠️ Status {response.status_code} - {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout: Backend took too long to respond")
        except requests.exceptions.ConnectionError:
            logger.error("❌ Connection Error: Cannot reach backend")
        except Exception as e:
            logger.error(f"❌ Ping failed: {str(e)}")
    
    def start(self):
        """Start the keep-alive scheduler"""
        try:
            logger.info("=" * 80)
            logger.info("🚀 KEEP-ALIVE SERVICE STARTED")
            logger.info("=" * 80)
            logger.info(f"Backend URL: {self.backend_url}")
            logger.info(f"Health Endpoint: {self.health_endpoint}")
            logger.info(f"Ping Interval: {self.interval} seconds (every {self.interval // 60} minutes)")
            logger.info("=" * 80)
            
            # Add job to scheduler
            self.scheduler.add_job(
                self.ping_backend,
                'interval',
                seconds=self.interval,
                id='keep_alive_ping',
                name='Keep-alive ping',
                next_run_time=datetime.now(),  # Run immediately on start
            )
            
            # Start scheduler
            self.scheduler.start()
            logger.info("✅ Scheduler started - pinging every 5 minutes")
            
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the keep-alive scheduler"""
        logger.info("🛑 Stopping keep-alive service...")
        if self.scheduler.running:
            self.scheduler.shutdown()
        logger.info(f"📊 Total pings sent: {self.ping_count}")
        logger.info(f"Last ping: {self.last_ping_time}")
    
    def get_status(self):
        """Get current status"""
        return {
            "status": "running" if self.scheduler.running else "stopped",
            "ping_count": self.ping_count,
            "last_ping": self.last_ping_time,
            "last_status_code": self.last_status_code,
            "backend_url": self.backend_url,
            "interval": self.interval,
        }


# Global service instance
keep_alive_service = None


def start_keep_alive(backend_url: str):
    """Initialize and start keep-alive service"""
    global keep_alive_service
    
    if keep_alive_service is not None and keep_alive_service.scheduler.running:
        logger.info("Keep-alive service is already running.")
        return

    keep_alive_service = KeepAliveService(
        backend_url=backend_url,
        interval=PING_INTERVAL
    )
    keep_alive_service.start()


def stop_keep_alive():
    """Stop keep-alive service"""
    global keep_alive_service
    
    if keep_alive_service:
        keep_alive_service.stop()
        keep_alive_service = None


if __name__ == "__main__":
    """
    Run as standalone service
    Usage: python keep_alive.py [BACKEND_URL]
    """
    url = sys.argv[1] if len(sys.argv) > 1 else RENDER_BACKEND_URL
    start_keep_alive(url)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        stop_keep_alive()
        sys.exit(0)
