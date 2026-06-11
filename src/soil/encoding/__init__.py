"""
Functionality to encode messages for frame connections.
"""

from .encoding import MessageEncoding
from .json import JsonEncoding

__all__ = [
    'MessageEncoding',
    'JsonEncoding'
]