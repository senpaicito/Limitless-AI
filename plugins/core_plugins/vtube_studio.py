import json
import logging
import websockets
import asyncio
import threading
from typing import Dict, Any, Optional
from plugins.plugin_base import PluginBase

class VTubeStudioPlugin(PluginBase):
    """VTube Studio integration for AI Companion"""
    
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        super().__init__(config, character_manager, memory_manager, ai_engine)
        self.websocket = None
        self.websocket_thread = None
        self.loop = None
        self.authenticated = False
        self.current_expression = "neutral"
        
    def get_name(self) -> str:
        return "vtube_studio"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def initialize(self) -> bool:
        """Initialize VTube Studio connection"""
        if not self.config.get('integrations.vtube_studio.enabled', False):
            self.logger.info("VTube Studio integration is disabled in configuration")
            return True
            
        try:
            # Start WebSocket connection in separate thread
            self.loop = asyncio.new_event_loop()
            self.websocket_thread = threading.Thread(target=self.run_websocket, daemon=True)
            self.websocket_thread.start()
            
            self.logger.info("VTube Studio plugin initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize VTube Studio plugin: {e}")
            return False
            
    async def connect_websocket(self):
        """Connect to VTube Studio WebSocket"""
        websocket_url = self.config.get('integrations.vtube_studio.websocket_url', 'ws://localhost:8001')
        
        try:
            self.websocket = await websockets.connect(websocket_url)
            self.logger.info(f"Connected to VTube Studio at {websocket_url}")
            
            # Authenticate with VTube Studio
            await self.authenticate()
            
            # Main message loop
            await self.message_loop()
            
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
            
    async def authenticate(self):
        """Authenticate with VTube Studio API"""
        try:
            # Request authentication token
            auth_request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "auth_request",
                "messageType": "AuthenticationTokenRequest",
                "data": {
                    "pluginName": "AI Companion",
                    "pluginDeveloper": "AI Companion Team"
                }
            }
            
            await self.websocket.send(json.dumps(auth_request))
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("messageType") == "AuthenticationTokenResponse":
                auth_token = response_data["data"]["authenticationToken"]
                
                # Use the authentication token
                auth_use_request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "auth_use",
                    "messageType": "AuthenticationRequest",
                    "data": {
                        "pluginName": "AI Companion",
                        "pluginDeveloper": "AI Companion Team",
                        "authenticationToken": auth_token
                    }
                }
                
                await self.websocket.send(json.dumps(auth_use_request))
                auth_response = await self.websocket.recv()
                auth_response_data = json.loads(auth_response)
                
                if auth_response_data.get("data", {}).get("authenticated"):
                    self.authenticated = True
                    self.logger.info("Successfully authenticated with VTube Studio")
                else:
                    self.logger.error("Failed to authenticate with VTube Studio")
                    
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            
    async def message_loop(self):
        """Main WebSocket message loop"""
        try:
            while self.websocket and not self.websocket.closed:
                message = await self.websocket.recv()
                await self.handle_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("VTube Studio connection closed")
        except Exception as e:
            self.logger.error(f"Message loop error: {e}")
            
    async def handle_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get("messageType")
            
            # Handle different message types as needed
            if message_type == "APIError":
                self.logger.error(f"VTube Studio API error: {data}")
                
        except Exception as e:
            self.logger.error(f"Error handling VTube Studio message: {e}")
            
    async def set_expression(self, expression: str, strength: float = 1.0):
        """Set facial expression in VTube Studio"""
        if not self.authenticated or not self.websocket:
            return
            
        try:
            # Map emotional states to VTube Studio expressions
            expression_map = {
                "joy": "happy",
                "sadness": "sad", 
                "anger": "angry",
                "fear": "fear",
                "surprise": "surprised",
                "curiosity": "thinking",
                "excitement": "excited",
                "contentment": "content",
                "neutral": "idle"
            }
            
            vts_expression = expression_map.get(expression, "idle")
            
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": f"expression_{vts_expression}",
                "messageType": "ExpressionActivationRequest",
                "data": {
                    "expressionFile": f"{vts_expression}.exp3.json",
                    "active": True
                }
            }
            
            await self.websocket.send(json.dumps(request))
            self.current_expression = expression
            
        except Exception as e:
            self.logger.error(f"Error setting expression: {e}")
            
    async def trigger_hotkey(self, hotkey_name: str):
        """Trigger a VTube Studio hotkey"""
        if not self.authenticated or not self.websocket:
            return
            
        try:
            request = {
                "apiName": "VTubeStudioPublicAPI", 
                "apiVersion": "1.0",
                "requestID": f"hotkey_{hotkey_name}",
                "messageType": "HotkeyTriggerRequest",
                "data": {
                    "hotkeyID": hotkey_name
                }
            }
            
            await self.websocket.send(json.dumps(request))
            
        except Exception as e:
            self.logger.error(f"Error triggering hotkey: {e}")
            
    def run_websocket(self):
        """Run WebSocket connection in separate thread"""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.connect_websocket())
        except Exception as e:
            self.logger.error(f"WebSocket thread error: {e}")
        finally:
            self.loop.close()
            
    def on_message_sent(self, message: str, message_type: str = "ai") -> None:
        """Update VTube Studio expression based on emotional state"""
        if not self.authenticated or message_type != "ai":
            return
            
        # Get current emotional state from AI engine
        emotional_state = self.ai_engine.current_emotional_state
        primary_emotion = emotional_state['primary_emotion']
        intensity = emotional_state['intensity']
        
        # Only update expression if intensity is significant
        if intensity > 0.3:
            asyncio.run_coroutine_threadsafe(
                self.set_expression(primary_emotion.value, intensity),
                self.loop
            )
            
    def cleanup(self):
        """Cleanup VTube Studio connection"""
        if self.websocket:
            try:
                asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
            except:
                pass
                
        if self.websocket_thread:
            self.websocket_thread.join(timeout=5.0)
            
        self.logger.info("VTube Studio plugin cleaned up")
        
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'integrations.vtube_studio.enabled': {
                'type': 'boolean',
                'default': False,
                'description': 'Enable VTube Studio integration'
            },
            'integrations.vtube_studio.websocket_url': {
                'type': 'string',
                'default': 'ws://localhost:8001',
                'description': 'VTube Studio WebSocket URL'
            }
        }