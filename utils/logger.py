import logging
import sys
from pathlib import Path

class UnicodeStreamHandler(logging.StreamHandler):
    """Custom stream handler that handles Unicode/emoji characters in Windows"""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Handle Unicode encoding issues
            if hasattr(stream, 'buffer'):
                # For stdout/stderr that support binary
                stream.buffer.write(msg.encode('utf-8', errors='replace') + self.terminator.encode('utf-8'))
            else:
                # Fallback for other streams
                stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

def setup_logging(debug: bool = False, log_file: str = "ai_companion.log"):
    """Setup logging configuration with Unicode support"""
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set log level
    level = logging.DEBUG if debug else logging.INFO
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (always UTF-8)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler with Unicode support
    console_handler = UnicodeStreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Reduce verbosity for some noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Test logging
    logger.info("Logging setup complete with Unicode support")
    
    return logger