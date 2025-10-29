#!/usr/bin/env python3
"""
AI Companion - Main Entry Point
A locally hosted, Python-based AI companion using Ollama
"""

import logging
import signal
import sys
import time
from utils.logger import setup_logging
from ai_engine import AIEngine
from webui.webui_stub import WebUIStub

class AICompanion:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_engine = None
        self.webui = None
        self.running = False
        
    def initialize(self) -> bool:
        """Initialize the AI Companion application"""
        try:
            self.logger.info("Starting AI Companion...")
            
            # Initialize AI Engine
            self.ai_engine = AIEngine()
            if not self.ai_engine.initialize():
                self.logger.error("Failed to initialize AI Engine")
                return False
                
            # Initialize WebUI (stub for Phase 1)
            self.webui = WebUIStub(
                self.ai_engine.config,
                self.ai_engine.character_manager, 
                self.ai_engine.memory_manager,
                self.ai_engine
            )
            self.webui.initialize()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.logger.info("AI Companion initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Companion: {e}")
            return False
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        
    def run(self) -> None:
        """Main application loop"""
        self.running = True
        
        # Start WebUI if enabled (Phase 2)
        if self.webui and self.webui.enabled:
            self.webui.start()
            
        # Start CLI interface if available
        cli_plugin = self.ai_engine.plugin_manager.get_plugin("cli_interface")
        if cli_plugin:
            cli_plugin.start_interactive_mode()
            
        # Main loop
        while self.running and not self.ai_engine.shutdown_flag:
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
                
        self.shutdown()
        
    def shutdown(self) -> None:
        """Shutdown the application"""
        self.logger.info("Shutting down AI Companion...")
        self.running = False
        
        if self.ai_engine:
            self.ai_engine.shutdown()
            
        if self.webui:
            self.webui.stop()
            
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