"""
Console encoding handler for Windows compatibility.
This module ensures proper encoding for console output on Windows systems.
"""

import sys
import os

def setup_console_encoding():
    """
    Set up proper console encoding for Windows systems.
    This prevents Unicode encoding errors when printing to console.
    """
    if sys.platform == 'win32':
        # Set console code page to UTF-8
        os.system('chcp 65001 >nul 2>&1')
        
        # Reconfigure stdout and stderr with UTF-8 encoding (if available)
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            # Fallback: just set environment variable
            pass
        
        # Set environment variable for Python
        os.environ['PYTHONIOENCODING'] = 'utf-8'

# Automatically setup encoding when module is imported
setup_console_encoding()
