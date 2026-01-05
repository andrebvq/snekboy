from enum import Enum, auto
from multiprocessing.util import info
import opcode
from typing import Optional
from src.registers import Register
from src.utils import validate_byte, validate_word
from src.memory import Memory
from dataclasses import dataclass
from src.opcodes import OPCODES, CB_OPCODES
from src.instructions_impl import InstructionImplementations
from src.cpu_decoder import InstructionType, decode_instruction_params

class ArithmeticTarget(Enum):
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    H = auto()
    L = auto()
    IMMEDIATE = auto()
    HL_INDIRECT = auto()

class InstructionType(Enum):
    ADD = auto()
    SUB = auto()
    INC = auto()
    DEC = auto()
    LD = auto()
    JP = auto()
    JR = auto()
    CALL = auto()
    RET = auto()
    PUSH = auto()
    POP = auto()
    NOP = auto()
    HALT = auto()

@dataclass
class Instruction:
    type: InstructionType
    target: Optional[ArithmeticTarget] = None
    immediate_value: Optional[int] = None  # For immediate values
    opcode: int = 0  # The actual opcode byte
    length: int = 1  # Instruction length in bytes
    cycles: int = 4  # Clock cycles

class CPU(InstructionImplementations):
    def __init__(self, memory = None):
        self.registers = Register()
        self.memory = memory if memory else Memory()
        self.total_cycles = 0
        self.halted = False
        self._initialize_state()

    def _initialize_state(self):
        """Initialize to Game Boy boot state"""
        self.registers._a = validate_byte(self.registers._a)
        self.registers._b = validate_byte(self.registers._b)
        self.registers._c = validate_byte(self.registers._c)
        self.registers._d = validate_byte(self.registers._d)
        self.registers._e = validate_byte(self.registers._e)
        self.registers._h = validate_byte(self.registers._h)
        self.registers._l = validate_byte(self.registers._l)
        self.registers._sp = validate_word(self.registers._sp)
        self.registers._pc = validate_word(self.registers._pc)

        self.registers.flags.zero = True
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = True
        self.registers.flags.carry = True

    def fetch_byte(self) -> int:
        """Fetch next byte from memory at PC and increment PC"""
        value = self.memory.read_byte(self.registers._pc)
        self.registers._pc = validate_word(self.registers._pc + 1)
        return value
    
    def fetch_word(self) -> int:
        """Fetch next word (16-bit) from memory at PC and increment PC"""
        value = self.memory.read_word(self.registers._pc)
        self.registers._pc = validate_word(self.registers._pc + 2)
        return value
    
    def decode(self, opcode: int):
        """Decode opcode into instruction parameters"""
        if opcode not in OPCODES:
            raise ValueError(f"Unknown opcode: 0x{opcode:02X} at PC=0x{self.registers._pc - 1:04X}")

        # Get opcode info
        info = OPCODES[opcode]
        name, length, cycles, flags = info

        # Decode parameters
        instr_type, target, immediate = decode_instruction_params(
            opcode,
            self.fetch_byte,
            self.fetch_word
        )

        if instr_type is None:
            raise NotImplementedError(
                f"Opcode 0x{opcode:02X} ({name}) not yet implemented at PC=0x{self.registers._pc - 1:04X}"
        )

        return (instr_type, target, immediate, cycles)
    
    def _decode_opcode(self, opcode: int, name: str, length: int, cycles: int) -> Instruction:
        """Decode specific opcode into Instruction object"""
        
        # NOP
        if opcode == 0x00:
            return Instruction(type=InstructionType.NOP, opcode=opcode, length=length, cycles=cycles)
        
        # HALT
        if opcode == 0x76:
            return Instruction(type=InstructionType.HALT, opcode=opcode, length=length, cycles=cycles)
        

        # ===== LD INSTRUCTIONS =====
    
        # LD r,n (immediate to register) - 0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E
        if opcode in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E]:
            immediate = self.fetch_byte()
            target_map = {
                0x06: 'B',
                0x0E: 'C',
                0x16: 'D',
                0x1E: 'E',
                0x26: 'H',
                0x2E: 'L',
                0x3E: 'A',
            }
            return Instruction(
                type=InstructionType.LD,
                target=target_map[opcode],  # Store as string for now
                immediate_value=immediate,
                opcode=opcode,
                length=length,
                cycles=cycles
            )
    
        # LD A,r (register to A) - 0x78-0x7F
        if 0x78 <= opcode <= 0x7F:
            source_map = {
                0x78: 'B',
                0x79: 'C',
                0x7A: 'D',
                0x7B: 'E',
                0x7C: 'H',
                0x7D: 'L',
                0x7E: '(HL)',  # Memory indirect
                0x7F: 'A',
            }
            return Instruction(
                type=InstructionType.LD,
                target='A',
                immediate_value=source_map[opcode],  # Use immediate_value to store source
                opcode=opcode,
                length=length,
                cycles=cycles
            )
    
        # LD rr,nn (16-bit immediate) - 0x01, 0x11, 0x21, 0x31
        if opcode in [0x01, 0x11, 0x21, 0x31]:
            immediate = self.fetch_word()
            target_map = {
                0x01: 'BC',
                0x11: 'DE',
                0x21: 'HL',
                0x31: 'SP',
            }
            return Instruction(
                type=InstructionType.LD,
                target=target_map[opcode],
                immediate_value=immediate,
                opcode=opcode,
                length=length,
                cycles=cycles
            )
    
        # LD (BC),A - 0x02
        if opcode == 0x02:
            return Instruction(
                type=InstructionType.LD,
                target='(BC)',
                immediate_value='A',
                opcode=opcode,
                length=length,
                cycles=cycles
            )
    
        # LD (DE),A - 0x12
        if opcode == 0x12:
            return Instruction(
                type=InstructionType.LD,
                target='(DE)',
                immediate_value='A',
                opcode=opcode,
                length=length,
                cycles=cycles
            )
    
        # LD (HL),A - 0x77
        if opcode == 0x77:
            return Instruction(
                type=InstructionType.LD,
                target='(HL)',
                immediate_value='A',
                opcode=opcode,
                length=length,
                cycles=cycles
            )
    
        # LD A,(BC) - 0x0A
        if opcode == 0x0A:
            return Instruction(
                type=InstructionType.LD,
                target='A',
                immediate_value='(BC)',
                opcode=opcode,
                length=length,
                cycles=cycles
            )
    
        # LD A,(DE) - 0x1A
        if opcode == 0x1A:
            return Instruction(
                type=InstructionType.LD,
                target='A',
                immediate_value='(DE)',
                opcode=opcode,
                length=length,
                cycles=cycles
            )

        # ADD A,r instructions (0x80-0x87)
        if 0x80 <= opcode <= 0x87:
            target_map = {
                0x80: ArithmeticTarget.B,
                0x81: ArithmeticTarget.C,
                0x82: ArithmeticTarget.D,
                0x83: ArithmeticTarget.E,
                0x84: ArithmeticTarget.H,
                0x85: ArithmeticTarget.L,
                0x86: ArithmeticTarget.HL_INDIRECT,  # ADD A,(HL)
                0x87: ArithmeticTarget.A,
            }
            return Instruction(
                type=InstructionType.ADD,
                target=target_map[opcode],
                opcode=opcode,
                length=length,
                cycles=cycles
            )
        
        # ADD A,n (immediate)
        if opcode == 0xC6:
            immediate = self.fetch_byte()
            return Instruction(
                type=InstructionType.ADD,
                target=ArithmeticTarget.IMMEDIATE,
                immediate_value=immediate,
                opcode=opcode,
                length=length,
                cycles=cycles
            )
        
        # Default: unimplemented instruction
        return Instruction(
            type=InstructionType.NOP,
            opcode=opcode,
            length=length,
            cycles=cycles
        )
    
    def step(self) -> int:
        """Execute one instruction"""
        if self.halted:
            return 4

        # FETCH
        opcode = self.fetch_byte()

        # DECODE
        instr_type, target, immediate, cycles = self.decode(opcode)

        # EXECUTE
        self.execute_instruction(instr_type, target, immediate)

        # UPDATE
        self.total_cycles += cycles

        return cycles
    
    def run_until(self, max_cycles: int) -> None:
        """Run CPU for a specified number of cycles"""
        target_cycles = self.total_cycles + max_cycles
        while self.total_cycles < target_cycles and not self.halted:
            self.step()

    def execute(self, instruction: Instruction) -> None:
        """Execute decoded instruction"""
        if instruction.type == InstructionType.NOP:
            pass  # Do nothing
        
        elif instruction.type == InstructionType.HALT:
            self.halted = True

        elif instruction.type == InstructionType.LD:
            self._execute_ld(instruction.target, instruction.immediate_value)
        
        elif instruction.type == InstructionType.ADD:
            self._execute_add(instruction.target, instruction.immediate_value)
        
        # Add more instruction types as you implement them
        else:
            raise NotImplementedError(f"Instruction type {instruction.type} not implemented")
        

    def _execute_ld(self, target, source) -> None:
        """Execute LD (load) instruction"""
    
        # Get source value
        if isinstance(source, int):
            # Immediate value
            value = source
        elif source == 'A':
            value = self.registers._a
        elif source == 'B':
            value = self.registers._b
        elif source == 'C':
            value = self.registers._c
        elif source == 'D':
            value = self.registers._d
        elif source == 'E':
            value = self.registers._e
        elif source == 'H':
            value = self.registers._h
        elif source == 'L':
            value = self.registers._l
        elif source == '(HL)':
        # Read from memory at address HL
            value = self.memory.read_byte(self.registers.hl)
        elif source == '(BC)':
            value = self.memory.read_byte(self.registers.bc)
        elif source == '(DE)':
            value = self.memory.read_byte(self.registers.de)
        else:
            raise ValueError(f"Unknown LD source: {source}")
    
        # Store to target
        if target == 'A':
            self.registers._a = validate_byte(value)
        elif target == 'B':
            self.registers._b = validate_byte(value)
        elif target == 'C':
            self.registers._c = validate_byte(value)
        elif target == 'D':
            self.registers._d = validate_byte(value)
        elif target == 'E':
            self.registers._e = validate_byte(value)
        elif target == 'H':
            self.registers._h = validate_byte(value)
        elif target == 'L':
            self.registers._l = validate_byte(value)
        elif target == 'BC':
            self.registers.bc = validate_word(value)
        elif target == 'DE':
            self.registers.de = validate_word(value)
        elif target == 'HL':
            self.registers.hl = validate_word(value)
        elif target == 'SP':
            self.registers._sp = validate_word(value)
        elif target == '(HL)':
        # Write to memory at address HL
            self.memory.write_byte(self.registers.hl, validate_byte(value))
        elif target == '(BC)':
            self.memory.write_byte(self.registers.bc, validate_byte(value))
        elif target == '(DE)':
            self.memory.write_byte(self.registers.de, validate_byte(value))
        else:
            raise ValueError(f"Unknown LD target: {target}")
    
    # LD doesn't affect flags
    
    def _execute_add(self, target: Optional[ArithmeticTarget], immediate_value: Optional[int] = None) -> None:
        """Execute ADD instruction"""
        if target is None:
            return
        
        # Get value to add
        if target == ArithmeticTarget.IMMEDIATE:
            value_to_add = immediate_value if immediate_value is not None else 0
        elif target == ArithmeticTarget.HL_INDIRECT:
            # Read from memory at address HL
            value_to_add = self.memory.read_byte(self.registers.hl)
        else:
            # Register target
            value_to_add = {
                ArithmeticTarget.A: self.registers._a,
                ArithmeticTarget.B: self.registers._b,
                ArithmeticTarget.C: self.registers._c,
                ArithmeticTarget.D: self.registers._d,
                ArithmeticTarget.E: self.registers._e,
                ArithmeticTarget.H: self.registers._h,
                ArithmeticTarget.L: self.registers._l,
            }.get(target, 0)
        
        # Perform addition
        current_a = self.registers._a
        result = current_a + value_to_add
        
        # Set flags
        self.registers.flags.zero = (result & 0xFF) == 0
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = (current_a & 0xF) + (value_to_add & 0xF) > 0xF
        self.registers.flags.carry = result > 0xFF
        
        # Store result
        self.registers._a = validate_byte(result)

    def _execute_sub(self, target, immediate_value=None) -> None:
        """Execute SUB instruction"""
        value = self._get_operand_value(target, immediate_value)

        current_a = self.registers._a
        result = current_a - value

        # Set flags
        self.registers.flags.zero = (result & 0xFF) == 0
        self.registers.flags.subtract = True  # Different from ADD
        self.registers.flags.half_carry = (current_a & 0xF) < (value & 0xF)
        self.registers.flags.carry = result < 0

        # Store result
        self.registers._a = validate_byte(result)

    def execute_instruction(self, instr_type, target, immediate):
        """Dispatch instruction to appropriate handler"""

        if instr_type == InstructionType.NOP:
            pass

        elif instr_type == InstructionType.HALT:
            self.halted = True
        
        elif instr_type == InstructionType.STOP:
            self.halted = True  # Similar to HALT for now

        elif instr_type == InstructionType.ADD:
            self._execute_add(target, immediate)
        
        elif instr_type == InstructionType.SUB:
            self._execute_sub(target, immediate)

        elif instr_type == InstructionType.AND:
            self._execute_and(target, immediate)

        elif instr_type == InstructionType.OR:
            self._execute_or(target, immediate)

        elif instr_type == InstructionType.XOR:
            self._execute_xor(target, immediate)

        elif instr_type == InstructionType.CP:
            self._execute_cp(target, immediate)
        elif instr_type == InstructionType.INC:
            self._execute_inc(target)

        elif instr_type == InstructionType.DEC:
            self._execute_dec(target)
        
        elif instr_type == InstructionType.LD:
            self._execute_ld(target, immediate)

        elif instr_type == InstructionType.PUSH:
            self._execute_push(target)

        elif instr_type == InstructionType.POP:
            self._execute_pop(target)

        elif instr_type == InstructionType.SCF:
            self._execute_scf()

        elif instr_type == InstructionType.CCF:
            self._execute_ccf()

        elif instr_type == InstructionType.CPL:
            self._execute_cpl()

        elif instr_type == InstructionType.DAA:
            self._execute_daa()

        elif instr_type == InstructionType.DI:
            self._execute_di()

        elif instr_type == InstructionType.EI:
            self._execute_ei()

        else:
            raise NotImplementedError(f"Instruction {instr_type} not implemented")

    def __str__(self) -> str:
        return (f"A: {self.registers._a:02X} "
                f"B: {self.registers._b:02X} "
                f"C: {self.registers._c:02X} "
                f"D: {self.registers._d:02X} "
                f"E: {self.registers._e:02X} "
                f"F: {self.registers.flags.to_byte():02X} "
                f"AF: {self.registers.af:04X} "
                f"BC: {self.registers.bc:04X} "
                f"DE: {self.registers.de:04X} "
                f"HL: {self.registers.hl:04X} "
                f"SP: {self.registers._sp:04X} "
                f"PC: {self.registers._pc:04X}"
                f"Cycles: {self.total_cycles}")