import json
import yaml
from typing import Any, Dict, List
from pathlib import Path

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Error loading JSON file {file_path}: {e}")

def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """Save JSON file safely"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False

def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load YAML file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"Error loading YAML file {file_path}: {e}")

def save_yaml_file(data: Dict[str, Any], file_path: str) -> bool:
    """Save YAML file safely"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving YAML file {file_path}: {e}")
        return False

def ensure_directory(path: str) -> Path:
    """Ensure directory exists"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def format_timestamp(timestamp: float) -> str:
    """Format timestamp for display"""
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."