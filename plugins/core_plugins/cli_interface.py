import logging
import threading
import time
from plugins.plugin_base import PluginBase

class CLInterfacePlugin(PluginBase):
    """Core plugin for command-line interface"""
    
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        super().__init__(config, character_manager, memory_manager, ai_engine)
        self.running = False
        self.input_thread = None
        
    def get_name(self) -> str:
        return "cli_interface"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def initialize(self) -> bool:
        self.logger.info("Initializing CLI Interface Plugin")
        self.running = True
        return True
        
    def cleanup(self) -> None:
        self.logger.info("Cleaning up CLI Interface Plugin")
        self.running = False
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)
            
    def start_interactive_mode(self) -> None:
        """Start interactive CLI mode"""
        self.logger.info("Starting interactive CLI mode")
        
        character_name = self.character_manager.get_name()
        print(f"\n🤖 {character_name} is ready to chat!")
        print("Type 'quit', 'exit', or 'bye' to end the conversation")
        print("-" * 50)
        
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        
    def _input_loop(self) -> None:
        """Main input loop for CLI interface"""
        while self.running:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                    
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print(f"\n{self.character_manager.get_name()}: Goodbye! It was nice talking with you! 👋")
                    # Signal the main application to shutdown
                    self.ai_engine.shutdown_flag = True
                    break
                    
                # Broadcast message received
                self.broadcast_message_received(user_input, "user")
                
                # Get AI response
                response = self.ai_engine.process_message(user_input)
                
                # Broadcast message sent
                self.broadcast_message_sent(response, "ai")
                
                print(f"\n{self.character_manager.get_name()}: {response}")
                
            except KeyboardInterrupt:
                print(f"\n\n{self.character_manager.get_name()}: Goodbye! 👋")
                self.ai_engine.shutdown_flag = True
                break
            except Exception as e:
                self.logger.error(f"Error in CLI input loop: {e}")
                print(f"\nError: {e}. Please try again.")
                
    def on_message_received(self, message: str, message_type: str = "user") -> None:
        """Handle message received events"""
        if message_type == "user" and self.running:
            # We already handle user input in the input loop, so just log it
            self.logger.debug(f"User message received: {message}")
            
    def on_message_sent(self, message: str, message_type: str = "ai") -> None:
        """Handle message sent events"""
        if message_type == "ai" and self.running:
            self.logger.debug(f"AI message sent: {message}")