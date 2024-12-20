from enum import Enum, auto
from typing import Optional
from registers import Register
from utils import validate_byte
from dataclasses import dataclass

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
        self.registers._a = validate_byte(self.registers._a)
        self.registers._b = validate_byte(self.registers._b)
        self.registers._c = validate_byte(self.registers._c)
        self.registers._d = validate_byte(self.registers._d)
        self.registers._e = validate_byte(self.registers._e)
        self.registers._h = validate_byte(self.registers._h)
        self.registers._l = validate_byte(self.registers._l)
        self.registers._sp = validate_byte(self.registers._sp)
        self.registers._pc = validate_byte(self.registers._pc)
        self.registers.flags.zero = False
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = False

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
                f"B: {self.registers._b:02X} "
                f"C: {self.registers._c:02X} "
                f"D: {self.registers._d:02X} "
                f"E: {self.registers._e:02X} "
                f"F: [{self.registers.flags}] "
                # study implementation of AF and revise below
                # f"AF: {self.registers._a:02X}{self.registers._flags:02X} "
                f"BC: {self.registers._b:02X}{self.registers._c:02X} "
                f"DE: {self.registers._d:02X}{self.registers._e:02X} "
                f"HL: {self.registers._h:02X}{self.registers._l:02X} "
                f"SP: {self.registers._sp:04X} "
                f"PC: {self.registers._pc:04X}")