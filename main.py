#!/usr/bin/env python3
"""
AI Companion - Main Entry Point with Integrated WebUI
"""

import logging
import signal
import sys
import time
import threading
from utils.logger import setup_logging
from ai_engine import AIEngine
from webui.app import WebUI

class AICompanion:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_engine = None
        self.webui = None
        self.webui_thread = None
        self.running = False
        
    def initialize(self) -> bool:
        """Initialize the AI Companion application"""
        try:
            self.logger.info("Starting AI Companion with Integrated WebUI...")
            
            # Initialize AI Engine
            self.ai_engine = AIEngine()
            if not self.ai_engine.initialize():
                self.logger.error("Failed to initialize AI Engine")
                return False
            
            # Initialize WebUI directly (not as plugin)
            # Access character_manager and memory_manager from the ai_engine
            self.webui = WebUI(
                self.ai_engine.config,
                self.ai_engine.character_manager,  # Fixed: access from ai_engine
                self.ai_engine.memory_manager,     # Fixed: access from ai_engine
                self.ai_engine
            )
            
            # Start WebUI in a separate thread
            self.webui_thread = threading.Thread(target=self.webui.start, daemon=True)
            self.webui_thread.start()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.logger.info("AI Companion with Integrated WebUI initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize AI Companion: %s", e)
            return False
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Received signal %s, shutting down...", signum)
        self.shutdown()
        
    def run(self) -> None:
        """Main application loop"""
        self.running = True
        
        host = self.ai_engine.config.get('webui.host', '127.0.0.1')
        port = self.ai_engine.config.get('webui.port', 5000)
        
        self.logger.info("=" * 60)
        self.logger.info("AI Companion is running!")
        self.logger.info("WebUI: http://%s:%s", host, port)
        self.logger.info("Open the above URL in your browser to start chatting")
        self.logger.info("=" * 60)
        
        # Main loop - just keep the application running
        while self.running and not self.ai_engine.shutdown_flag:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error("Error in main loop: %s", e)
                
        self.shutdown()
        
    def shutdown(self) -> None:
        """Shutdown the application"""
        self.logger.info("Shutting down AI Companion...")
        self.running = False
        
        # Stop WebUI
        if self.webui:
            self.webui.stop()
            
        # Shutdown AI Engine
        if self.ai_engine:
            self.ai_engine.shutdown()
            
        self.logger.info("AI Companion shutdown complete")
        
def main():
    """Main entry point"""
    # Setup logging
    setup_logging(debug=True)
    
    # Create and run application
    app = AICompanion()
    
    if app.initialize():
        app.run()
    else:
        logging.error("Failed to initialize AI Companion")
        sys.exit(1)
        
if __name__ == "__main__":
    main()