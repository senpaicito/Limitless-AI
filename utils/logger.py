import logging
import sys
from pathlib import Path

def setup_logging(debug: bool = False, log_file: str = "ai_companion.log"):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set log level
    level = logging.DEBUG if debug else logging.INFO
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce verbosity for some noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging setup complete")
    
    return logger