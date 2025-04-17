"""Utility functions for JobHuntGPT."""

import os
import logging
import yaml
from typing import Dict, Any, Optional, List
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        # Check if file exists
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
        
        # Load configuration
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str = "config.yaml") -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save the configuration file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
        
        # Save configuration
        with open(config_path, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        
        logger.info(f"Configuration saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from a nested configuration dictionary.
    
    Args:
        config: Configuration dictionary
        key_path: Path to the key, separated by dots (e.g. "llm.model_path")
        default: Default value to return if the key is not found
        
    Returns:
        Value from the configuration or default
    """
    try:
        # Split key path
        keys = key_path.split(".")
        
        # Traverse dictionary
        value = config
        for key in keys:
            if key not in value:
                return default
            value = value[key]
        
        return value
    except Exception as e:
        logger.error(f"Error getting configuration value: {e}")
        return default

def setup_logging(log_file: str = "jobhuntgpt.log", log_level: int = logging.INFO) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logger.info(f"Logging configured with level {log_level}")
    except Exception as e:
        print(f"Error setting up logging: {e}")

def create_directory_if_not_exists(directory: str) -> None:
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory: Directory path
    """
    try:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Directory created or already exists: {directory}")
    except Exception as e:
        logger.error(f"Error creating directory: {e}")

def save_json(data: Any, file_path: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save the JSON file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        
        # Save data
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
        
        logger.debug(f"Data saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")

def load_json(file_path: str) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Loaded data
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"JSON file not found: {file_path}")
            return None
        
        # Load data
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        return data
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        return None

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root directory
    """
    return Path(__file__).parent.parent

def get_data_dir() -> Path:
    """
    Get the data directory.
    
    Returns:
        Path to the data directory
    """
    root = get_project_root()
    data_dir = root / "data"
    create_directory_if_not_exists(str(data_dir))
    return data_dir

def get_output_dir() -> Path:
    """
    Get the output directory.
    
    Returns:
        Path to the output directory
    """
    root = get_project_root()
    output_dir = root / "output"
    create_directory_if_not_exists(str(output_dir))
    return output_dir

def get_model_dir() -> Path:
    """
    Get the model directory.
    
    Returns:
        Path to the model directory
    """
    root = get_project_root()
    model_dir = root / "models"
    create_directory_if_not_exists(str(model_dir))
    return model_dir
