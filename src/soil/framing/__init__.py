
"""
Functionality for connections that exchange frames.
"""

from .connection import FrameConnection
from .receiver import FrameReceiver

__all__ = [
    'FrameConnection',
    'FrameReceiver'
]