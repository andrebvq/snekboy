from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from utils import BitField, validate_byte

class FlagBit(Enum):
    ZERO = 7
    SUBTRACT = 6
    HALF_CARRY = 5
    CARRY = 4

class Flags:
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
        self._a: int = 0
        self._flags = Flags()
        self._b: int = 0
        self._c: int = 0
        self._d: int = 0
        self._e: int = 0
        self._h: int = 0
        self._l: int = 0
        self._sp: int = 0
        self._pc: int = 0

    @property
    def flags(self) -> Flags:
        return self._flags

    def __repr__(self) -> str:
        return (f"Register(a=0x{self._a:02x}, f=0x{self._flags.to_byte():02x}, "
                f"b=0x{self._b:02x}, c=0x{self._c:02x})")

class ArithmeticTarget(Enum):
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    H = auto()
    L = auto()

class InstructionType(Enum):
    ADD = auto()

@dataclass
class Instruction:
    type: InstructionType
    target: Optional[ArithmeticTarget] = None

class CPU:
    def __init__(self):
        self.registers = Register()
        self._initialize_state()

    def _initialize_state(self):
        #self.registers._a = 0x01
        self.registers.flags.zero = True
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = True
        self.registers.flags.carry = True

    def execute(self, instruction: Instruction) -> None:
        if instruction.type == InstructionType.ADD:
            self._execute_add(instruction.target)

    def _execute_add(self, target: Optional[ArithmeticTarget]) -> None:
        if target is None:
            return

        value_to_add = {
            ArithmeticTarget.B: self.registers._b,
            ArithmeticTarget.C: self.registers._c,
            ArithmeticTarget.D: self.registers._d,
            ArithmeticTarget.E: self.registers._e,
            ArithmeticTarget.H: self.registers._h,
            ArithmeticTarget.L: self.registers._l,
        }.get(target, 0)

        current_a = self.registers._a
        result = current_a + value_to_add

        self.registers.flags.zero = (result & 0xFF) == 0
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = (current_a & 0xF) + (value_to_add & 0xF) > 0xF
        self.registers.flags.carry = result > 0xFF

        self.registers._a = validate_byte(result)

    def __str__(self) -> str:
        return (f"A: {self.registers._a:02X} "
                f"F: [{self.registers.flags}] "
                f"BC: {self.registers._b:02X}{self.registers._c:02X} "
                f"DE: {self.registers._d:02X}{self.registers._e:02X} "
                f"HL: {self.registers._h:02X}{self.registers._l:02X} "
                f"SP: {self.registers._sp:04X} "
                f"PC: {self.registers._pc:04X}")

def test_flags():
    cpu = CPU()
    
    # Test flag operations
    print("Initial flags:", cpu.registers.flags)
    
    # Set some flags
    cpu.registers.flags.zero = True
    cpu.registers.flags.carry = True
    print("After setting Z and C:", cpu.registers.flags)
    
    # Clear a flag
    cpu.registers.flags.zero = False
    print("After clearing Z:", cpu.registers.flags)
    
    # Test flag byte conversion
    flag_byte = cpu.registers.flags.to_byte()
    print(f"Flags as byte: 0x{flag_byte:02X}")
    
    # Set flags from byte
    cpu.registers.flags.from_byte(0b11110000)
    print("After setting from byte:", cpu.registers.flags)

if __name__ == "__main__":
    cpu = CPU()
    print("Initial CPU state:")
    print(cpu)

    instruction = Instruction(InstructionType.ADD, ArithmeticTarget.B)
    cpu.execute(instruction)
    print("\nAfter ADD B:")
    print(cpu)

    test_flags()
