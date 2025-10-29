import discord
import logging
import asyncio
import threading
from typing import Dict, Any, List
from plugins.plugin_base import PluginBase

class DiscordBot(PluginBase):
    """Discord bot integration for AI Companion"""
    
    def __init__(self, config, character_manager, memory_manager, ai_engine):
        super().__init__(config, character_manager, memory_manager, ai_engine)
        self.bot = None
        self.loop = None
        self.bot_thread = None
        self.enabled_channels = set()
        
    def get_name(self) -> str:
        return "discord_bot"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def initialize(self) -> bool:
        """Initialize Discord bot"""
        if not self.config.get('integrations.discord.enabled', False):
            self.logger.info("Discord integration is disabled in configuration")
            return True
            
        token = self.config.get('integrations.discord.token', '')
        if not token:
            self.logger.error("Discord bot token not configured")
            return False
            
        try:
            # Setup Discord bot
            intents = discord.Intents.default()
            intents.message_content = True
            intents.messages = True
            
            self.bot = discord.Client(intents=intents)
            self.setup_handlers()
            
            # Start bot in a separate thread
            self.loop = asyncio.new_event_loop()
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            
            # Load enabled channels
            channel_id = self.config.get('integrations.discord.channel_id', '')
            if channel_id:
                self.enabled_channels.add(int(channel_id))
            
            self.logger.info("Discord bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Discord bot: {e}")
            return False
            
    def setup_handlers(self):
        """Setup Discord event handlers"""
        
        @self.bot.event
        async def on_ready():
            self.logger.info(f'Discord bot logged in as {self.bot.user.name}')
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=f"to {self.character_manager.get_name()}"
                )
            )
            
        @self.bot.event
        async def on_message(message):
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return
                
            # Check if this channel is enabled
            if self.enabled_channels and message.channel.id not in self.enabled_channels:
                return
                
            # Ignore messages that don't mention the bot (if not in DM)
            if isinstance(message.channel, discord.DMChannel):
                # Always respond in DMs
                await self.handle_message(message)
            elif self.bot.user in message.mentions:
                # Respond when mentioned in channels
                await self.handle_message(message)
                
    async def handle_message(self, message):
        """Handle incoming Discord messages"""
        try:
            # Remove bot mention from message content
            content = message.content
            if self.bot.user in message.mentions:
                for mention in message.mentions:
                    content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
                content = content.strip()
            
            if not content:
                return
                
            # Show typing indicator
            async with message.channel.typing():
                # Process message through AI engine
                response = self.ai_engine.process_message(content)
                
                # Split long messages if needed (Discord has 2000 char limit)
                if len(response) > 2000:
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(response)
                    
                # Broadcast events
                self.broadcast_message_received(content, "discord_user")
                self.broadcast_message_sent(response, "discord_ai")
                
        except Exception as e:
            self.logger.error(f"Error handling Discord message: {e}")
            await message.reply("I encountered an error processing your message. Please try again.")
            
    def run_bot(self):
        """Run the Discord bot in a separate thread"""
        asyncio.set_event_loop(self.loop)
        try:
            token = self.config.get('integrations.discord.token')
            self.loop.run_until_complete(self.bot.start(token))
        except Exception as e:
            self.logger.error(f"Discord bot error: {e}")
        finally:
            self.loop.close()
            
    def cleanup(self):
        """Cleanup Discord bot"""
        if self.bot and self.loop:
            try:
                self.loop.call_soon_threadsafe(self.bot.close)
                if self.bot_thread:
                    self.bot_thread.join(timeout=5.0)
            except Exception as e:
                self.logger.error(f"Error cleaning up Discord bot: {e}")
        self.logger.info("Discord bot cleaned up")
        
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'integrations.discord.enabled': {
                'type': 'boolean',
                'default': False,
                'description': 'Enable Discord bot integration'
            },
            'integrations.discord.token': {
                'type': 'string',
                'default': '',
                'description': 'Discord bot token'
            },
            'integrations.discord.channel_id': {
                'type': 'string', 
                'default': '',
                'description': 'Specific channel ID to listen to (empty for all channels)'
            }
        }
        
    def add_enabled_channel(self, channel_id: int):
        """Add a channel to the enabled channels list"""
        self.enabled_channels.add(channel_id)
        
    def remove_enabled_channel(self, channel_id: int):
        """Remove a channel from the enabled channels list"""
        self.enabled_channels.discard(channel_id)
        
    def get_enabled_channels(self) -> List[int]:
        """Get list of enabled channel IDs"""
        return list(self.enabled_channels)