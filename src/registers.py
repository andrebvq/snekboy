from dataclasses import dataclass
from enum import Enum
from src.utils import BitField, validate_byte, validate_word

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

        self._flags = Flags()
        self._a = 0x01  # 0x11 for GBC
        self._b = 0x00
        self._c = 0x13
        self._d = 0x00
        self._e = 0xD8
        self._h = 0x01
        self._l = 0x4D
        self._sp = 0xFFFE
        self._pc = 0x0100  # Cartridge entry point (start of program)

    @property
    def flags(self) -> Flags:
        return self._flags

    @property
    def af(self) -> int:
        """Get AF register pair (A in high byte, F in low byte)"""
        return (self._a << 8) | self._flags.to_byte()
    
    @af.setter
    def af(self, value: int) -> None:
        """Set AF register pair"""
        value = validate_word(value)  # Ensure 16-bit
        self._a = (value >> 8) & 0xFF  # High byte
        self._flags.from_byte(value & 0xFF)  # Low byte

    @property
    def bc(self) -> int:
        """Get BC register pair"""
        return (self._b << 8) | self._c
    
    @bc.setter
    def bc(self, value: int) -> None:
        """Set BC register pair"""
        value = validate_word(value)
        self._b = (value >> 8) & 0xFF
        self._c = value & 0xFF

    @property
    def de(self) -> int:
        """Get DE register pair"""
        return (self._d << 8) | self._e
    
    @de.setter
    def de(self, value: int) -> None:
        """Set DE register pair"""
        value = validate_word(value)
        self._d = (value >> 8) & 0xFF
        self._e = value & 0xFF

    @property
    def hl(self) -> int:
        """Get HL register pair"""
        return (self._h << 8) | self._l
    
    @hl.setter
    def hl(self, value: int) -> None:
        """Set HL register pair"""
        value = validate_word(value)
        self._h = (value >> 8) & 0xFF
        self._l = value & 0xFF

    def __repr__(self) -> str:
        return (f"Register(a=0x{self._a:02x}, f=0x{self._flags.to_byte():02x}, "
                f"b=0x{self._b:02x}, c=0x{self._c:02x})")
    
    def __repr__(self) -> str:
        return (f"Register(a=0x{self._a:02x}, f=0x{self._flags.to_byte():02x}, "
                f"b=0x{self._b:02x}, c=0x{self._c:02x}, "
                f"d=0x{self._d:02x}, e=0x{self._e:02x}, "
                f"h=0x{self._h:02x}, l=0x{self._l:02x}, "
                f"af=0x{self.af:04x}, bc=0x{self.bc:04x}, "
                f"de=0x{self.de:04x}, hl=0x{self.hl:04x})")
