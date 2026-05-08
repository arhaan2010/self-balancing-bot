"""
Utility Functions Module
"""

import logging
import yaml
import os
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger('self-balancing-bot')
    logger.setLevel(log_level)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    
    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger


def load_config(config_file):
    """
    Load configuration from YAML file
    
    Args:
        config_file: Path to YAML config file
    
    Returns:
        dict: Configuration dictionary
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def clamp(value, min_val, max_val):
    """
    Clamp a value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        float: Clamped value
    """
    return max(min_val, min(max_val, value))


def map_range(value, in_min, in_max, out_min, out_max):
    """
    Map a value from one range to another
    
    Args:
        value: Value to map
        in_min: Input range minimum
        in_max: Input range maximum
        out_min: Output range minimum
        out_max: Output range maximum
    
    Returns:
        float: Mapped value
    """
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class RollingAverage:
    """
    Rolling average filter
    """
    
    def __init__(self, window_size=5):
        """
        Initialize rolling average
        
        Args:
            window_size: Size of rolling window
        """
        self.window_size = window_size
        self.values = []
    
    def add(self, value):
        """
        Add a value to the rolling average
        
        Args:
            value: Value to add
        """
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
    
    def get_average(self):
        """
        Get the average of the values in the window
        
        Returns:
            float: Average value
        """
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)
    
    def reset(self):
        """
        Reset the rolling average
        """
        self.values = []
