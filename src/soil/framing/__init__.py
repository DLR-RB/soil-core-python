
"""
Functionality for connections that exchange frames.
"""

from .connection import FrameConnection
from .distributor import FrameDistributor
from .error import FramingError
from .framing import StreamFraming
from .receiver import FrameReceiver
from .sync import SyncByteLengthFraming

__all__ = [
    'FrameConnection',
    'FrameDistributor',
    'FramingError',
    'StreamFraming',
    'FrameReceiver',
    'SyncByteLengthFraming',
]