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

    def execute(self, instruction: Instruction) -> None:
        match instruction.type:
            case Instruction.Type.ADD:
                match instruction.target:
                    case ArithmeticTarget.C:
                        value = self.registers.c
                        

                    case _:
                        pass

            case _:
                pass


if __name__=="__main__":
    inst = Instruction(Instruction.Type.ADD, ArithmeticTarget.A)
    print(inst.type)
    print(inst.target)