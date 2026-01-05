from typing import Callable, TypeVar, Any

# Type aliases
Byte = int  # 8-bit unsigned (0-255)
Word = int  # 16-bit unsigned (0-65535)
T = TypeVar('T')

# bit validation and manipulation
def validate_byte(value: int) -> Byte:
    """Ensure value is a valid byte (0-255)"""
    return value & 0xFF

def validate_word(value: int) -> Word:
    """Ensure value is a valid word (0-65535)"""
    return value & 0xFFFF

def combine_bytes(high: Byte, low: Byte) -> Word:
    """Combine two bytes into a word (high byte, low byte)"""
    return (validate_byte(high) << 8) | validate_byte(low)

def split_word(word: Word) -> tuple[Byte, Byte]:
    """Split a word into high and low bytes"""
    word = validate_word(word)
    return (word >> 8) & 0xFF, word & 0xFF

def check_half_carry_add(a: Byte, b: Byte) -> bool:
    """Check if adding two bytes causes a half carry"""
    return (a & 0xF) + (b & 0xF) > 0xF

def check_half_carry_sub(a: Byte, b: Byte) -> bool:
    """Check if subtracting two bytes causes a half carry"""
    return (a & 0xF) - (b & 0xF) < 0

def check_carry_add(a: Byte, b: Byte) -> bool:
    """Check if adding two bytes causes a carry"""
    return a + b > 0xFF

def check_carry_sub(a: Byte, b: Byte) -> bool:
    """Check if subtracting two bytes causes a carry"""
    return a - b < 0

# bitfield-related
def get_bit(value: int, bit: int) -> bool:
    """Get the value of a specific bit"""
    # Note: shift right by 'bit' position
    # Check individual bit, ie. for flags
    return bool((value >> bit) & 1)

def set_bit(value: int, bit: int) -> int:
    """Set a specific bit to 1"""
    return value | (1 << bit)

def clear_bit(value: int, bit: int) -> int:
    """Clear a specific bit to 0"""
    return value & ~(1 << bit)

def modify_bit(value: int, bit: int, state: bool) -> int:
    """Set or clear a specific bit based on state"""
    return set_bit(value, bit) if state else clear_bit(value, bit)

class BitField:
    """Helper class for managing bit fields"""
    def __init__(self, value: int = 0):
        self._value = value

    @property
    def value(self) -> int:
        return self._value

    def get_bit(self, bit: int) -> bool:
        return get_bit(self._value, bit)

    def set_bit(self, bit: int) -> None:
        self._value = set_bit(self._value, bit)

    def clear_bit(self, bit: int) -> None:
        self._value = clear_bit(self._value, bit)

    def modify_bit(self, bit: int, state: bool) -> None:
        self._value = modify_bit(self._value, bit, state)

def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """Simple memoization decorator for pure functions"""
    cache = {}
    def memoized(*args: Any) -> T:
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return memoized

# Constants
BYTE_MAX = 0xFF
WORD_MAX = 0xFFFF

# Common GB-specific constants
CLOCK_SPEED = 4_194_304  # Hz
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
VBLANK_PERIOD = 70224  # Clock cycles

# Memory map constants
ROM_BANK_SIZE = 0x4000
RAM_BANK_SIZE = 0x2000
VRAM_SIZE = 0x2000
WRAM_SIZE = 0x2000
OAM_SIZE = 0xA0
IO_SIZE = 0x80
HRAM_SIZE = 0x7F

class MemoryRanges:
    """Memory map address ranges"""
    ROM_BANK_0_START = 0x0000
    ROM_BANK_0_END = 0x3FFF
    ROM_BANK_N_START = 0x4000
    ROM_BANK_N_END = 0x7FFF
    VRAM_START = 0x8000
    VRAM_END = 0x9FFF
    EXTERNAL_RAM_START = 0xA000
    EXTERNAL_RAM_END = 0xBFFF
    WRAM_START = 0xC000
    WRAM_END = 0xDFFF
    ECHO_RAM_START = 0xE000
    ECHO_RAM_END = 0xFDFF
    OAM_START = 0xFE00
    OAM_END = 0xFE9F
    IO_START = 0xFF00
    IO_END = 0xFF7F
    HRAM_START = 0xFF80
    HRAM_END = 0xFFFE
    IE_REGISTER = 0xFFFF
