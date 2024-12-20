from dataclasses import dataclass
from enum import Enum
from utils import BitField, validate_byte

class FlagBit(Enum):
    """CPU flag bit positions"""
    ZERO = 7       # Set when result is 0
    SUBTRACT = 6   # Set when subtraction was performed
    HALF_CARRY = 5 # Set when carry from bit 3 to 4 occurred
    CARRY = 4      # Set when carry occurred or req. for rotates

class Flags:
    """Class to manage CPU flags using BitField"""
    def __init__(self):
        self._bits = BitField()

    @property
    def zero(self) -> bool:
        return self._bits.get_bit(FlagBit.ZERO.value)
    
    @zero.setter
    def zero(self, value: bool) -> None:
        self._bits.modify_bit(FlagBit.ZERO.value, value)

    @property
    def subtract(self) -> bool:
        return self._bits.get_bit(FlagBit.SUBTRACT.value)
    
    @subtract.setter
    def subtract(self, value: bool) -> None:
        self._bits.modify_bit(FlagBit.SUBTRACT.value, value)

    @property
    def half_carry(self) -> bool:
        return self._bits.get_bit(FlagBit.HALF_CARRY.value)
    
    @half_carry.setter
    def half_carry(self, value: bool) -> None:
        self._bits.modify_bit(FlagBit.HALF_CARRY.value, value)

    @property
    def carry(self) -> bool:
        return self._bits.get_bit(FlagBit.CARRY.value)
    
    @carry.setter
    def carry(self, value: bool) -> None:
        self._bits.modify_bit(FlagBit.CARRY.value, value)

    def to_byte(self) -> int:
        return self._bits.value

    def from_byte(self, value: int) -> None:
        self._bits = BitField(validate_byte(value))

    def __str__(self) -> str:
        return (f"Z:{int(self.zero)} "
                f"N:{int(self.subtract)} "
                f"H:{int(self.half_carry)} "
                f"C:{int(self.carry)}")

class Register:
    def __init__(self):
        self._a: int = 255
        self._flags = Flags()
        self._b: int = 1
        self._c: int = 1
        self._d: int = 1
        self._e: int = 1
        self._h: int = 1
        self._l: int = 1
        self._sp: int = 0
        self._pc: int = 0

    @property
    def flags(self) -> Flags:
        return self._flags

    def __repr__(self) -> str:
        return (f"Register(a=0x{self._a:02x}, f=0x{self._flags.to_byte():02x}, "
                f"b=0x{self._b:02x}, c=0x{self._c:02x})")
