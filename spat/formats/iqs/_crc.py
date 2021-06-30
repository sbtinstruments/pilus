from typing import Callable

crc32: Callable[[bytes, int], int]

# Python contains two crc32 implementations:
#
#   1. `zlib.crc32`: Fast but depends in zlib
#   2. `binascii.crc32`: Slow but no dependencies
#
# We prefer (1) but fall back on (2).
try:
    from zlib import crc32
except ImportError:
    from binascii import crc32
