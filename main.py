from dataclasses import dataclass
from enum import Enum, auto
import numpy as np

class Register():
    def __init__(self):
        # ToDo? Force u8 type?
        self.a = 0 # Accumulator
        self.f = 0 # Cpu flag
        self.b = 0 # Generic
        self.c = 0 # Generic
        self.d = 0 # Generic
        self.e = 0 # Generic
        self.h = 0 # Memory
        self.l = 0 # Memory
        self.sp = 0 # Stack pointer
        self.pc = 0 # Program counter
    
    @property
    def af(self):
        # Combine AF
        # ToDo? Force u16 type?
        return (self.a << 8) | self.f
    
    @property
    def bc(self):
        # Combine BC
        return (self.b << 8) | self.c
    
    @property
    def de(self):
        # Combine DE
        return (self.d << 8) | self.e
    
    @property
    def hl(self):
        # Combine HL
        return (self.h << 8) | self.l

# Flags constants
ZERO_FLAG_BYTE_POSITION = 7
SUBTRACT_FLAG_BYTE_POSITION = 6
HALF_CARRY_FLAG_BYTE_POSITION = 5
CARRY_FLAG_BYTE_POSITION = 4

@dataclass
class FlagsRegister:
    zero: bool
    subtract: bool
    half_carry: bool
    carry: bool

    def to_byte(self) -> int:
        # Flags to byte -> u8
        return (
            (1 if self.zero else 0) << ZERO_FLAG_BYTE_POSITION |
            (1 if self.subtract else 0) << SUBTRACT_FLAG_BYTE_POSITION |
            (1 if self.half_carry else 0) << HALF_CARRY_FLAG_BYTE_POSITION |
            (1 if self.carry else 0) << CARRY_FLAG_BYTE_POSITION
        )

    @classmethod
    def from_byte(cls, byte: int) -> 'FlagsRegister':
        # Flags from byte -> ?
        return cls(
            zero=((byte >> ZERO_FLAG_BYTE_POSITION) & 0b1) != 0,
            subtract=((byte >> SUBTRACT_FLAG_BYTE_POSITION) & 0b1) != 0,
            half_carry=((byte >> HALF_CARRY_FLAG_BYTE_POSITION) & 0b1) != 0,
            carry=((byte >> CARRY_FLAG_BYTE_POSITION) & 0b1) != 0
        )

class ArithmeticTarget(Enum):
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    H = auto()
    L = auto()


@dataclass
class Instruction():
    class Type(Enum):
        ADD = auto()

    type: Type
    target: ArithmeticTarget | None = None


class CPU():
    def __init__(self):
        self.registers = Register

    def overflowing_add(value):
        return True if value > 255 else False

    def execute(self, instruction: Instruction) -> None:
        match instruction.type:

            case Instruction.Type.ADD:
                match instruction.target:
                    case ArithmeticTarget.B:
                        self.registers.a += self.registers.b
                    case ArithmeticTarget.C:
                        self.registers.a += self.registers.c
                    case ArithmeticTarget.D:
                        self.registers.a += self.registers.d
                    case ArithmeticTarget.E:
                        self.registers.a += self.registers.e                                            
                    case ArithmeticTarget.H:
                        self.registers.a += self.registers.h
                    case ArithmeticTarget.L:
                        self.registers.a += self.registers.l
                    case _:
                        pass

            case _:
                pass


if __name__=="__main__":
    inst = Instruction(Instruction.Type.ADD, ArithmeticTarget.A)
    print(inst.type)
    print(inst.target)