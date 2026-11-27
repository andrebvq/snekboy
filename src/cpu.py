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
from src.ppu import PPU
from src.gameboy_doctor import create_logger_if_enabled  # Gameboy Doctor integration

# Opcodes with no instruction on the SM83; executing one locks up the CPU.
ILLEGAL_OPCODES = frozenset({0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD})

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

# Note: InstructionType is imported from cpu_decoder, not defined here

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

        # Timer state - must be initialized before Memory
        # The Game Boy has an internal 16-bit counter that increments every T-cycle (M-cycle = 4 T-cycles)
        self._system_counter = 0  # Internal 16-bit counter
        self._prev_timer_bit = False  # Previous value of selected timer bit for edge detection
        self._timer_overflow_cycles = 0  # 1 while TIMA reads 0x00 after overflow, before the TMA reload
        self._tima_reloaded = False  # True if the most recent M-cycle reloaded TIMA from TMA

        # Create memory with reference to this CPU
        self.memory = memory if memory else Memory(cpu=self)
        self.memory._cpu = self   # a Memory passed in must also reach the CPU's timer

        # Create PPU with reference to memory and interrupt callback
        self.ppu = PPU(self.memory, self._request_interrupt)

        self.total_cycles = 0
        self.halted = False
        self.ime = False  # Interrupt Master Enable flag
        self._ei_pending = 0  # EI delay counter: counts down to 0 before enabling IME
        self._halt_bug_active = False  # HALT bug: skip next PC increment
        self._acc = 0      # T-cycles started in the current instruction
        self._synced = 0   # T-cycles the timer/PPU/DMA have been advanced to
        self.locked = False  # Set by an illegal opcode; the CPU stops until reset
        self.stopped = False  # STOP mode: CPU and timer frozen until a button is pressed

        # Gameboy Doctor: Create logger if enabled (None if disabled)
        self._doctor_logger = create_logger_if_enabled()

        self._initialize_state()

    def simulate_boot(self):
        """
        Simulate boot ROM execution

        Call this after loading ROM but before starting execution.
        Clears VRAM, initializes registers, and sets up post-boot state.
        """
        # Simulate boot ROM hardware initialization
        self.memory.simulate_boot_rom()

        # Re-initialize CPU to post-boot state
        self._initialize_state()

        # DIV is the top byte of the internal 16-bit counter, so seed the
        # counter itself (DMG-ABC value after the boot ROM; DIV reads 0xAB).
        self._system_counter = 0xABCC
        self.memory._data[0xFF04] = self._system_counter >> 8

    def _initialize_state(self):
        """
        Initialize to post-boot ROM state (what registers contain after boot completes)

        Real Game Boy boot ROM sets these values before jumping to cartridge at 0x0100:
        - A = 0x01 (DMG), 0x11 (Game Boy Pocket), 0xFF (Game Boy Color in DMG mode)
        - F = 0xB0 (Z=1, N=0, H=1, C=1)
        - BC = 0x0013
        - DE = 0x00D8
        - HL = 0x014D
        - SP = 0xFFFE
        - PC = 0x0100 (cartridge entry point)
        """
        # Post-boot register values for DMG (original Game Boy)
        self.registers._a = 0x01  # DMG identifier
        self.registers._b = 0x00
        self.registers._c = 0x13
        self.registers._d = 0x00
        self.registers._e = 0xD8
        self.registers._h = 0x01
        self.registers._l = 0x4D
        self.registers._sp = 0xFFFE
        self.registers._pc = 0x0100  # Start at cartridge entry point

        # Flags: Z=1, N=0, H=1, C=1 (F = 0xB0)
        self.registers.flags.zero = True
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = True
        self.registers.flags.carry = True

    def fetch_byte(self) -> int:
        """Fetch next byte from memory at PC and increment PC"""
        value = self._read(self.registers._pc)

        # HALT bug: skip PC increment once
        if self._halt_bug_active:
            self._halt_bug_active = False
            # Don't increment PC - instruction will be fetched again next time
        else:
            self.registers._pc = validate_word(self.registers._pc + 1)

        return value
    
    def fetch_word(self) -> int:
        """Fetch next word (16-bit) from memory at PC and increment PC"""
        pc = self.registers._pc
        value = self._read(pc) | (self._read((pc + 1) & 0xFFFF) << 8)
        self.registers._pc = validate_word(pc + 2)
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

        # CB instructions need special cycle handling
        # Different CB instructions have different timings for (HL):
        # - BIT b,(HL): 12 T-cycles (read only)
        # - SET/RES/Rotate/Shift (HL): 16 T-cycles (read + write)
        # - Register operations: 8 T-cycles
        if opcode == 0xCB:
            if target == '(HL)':
                # Check if it's a BIT instruction (read-only)
                if instr_type == InstructionType.BIT:
                    cycles = 12  # BIT b,(HL) - read only
                else:
                    cycles = 16  # SET/RES/Rotate/Shift (HL) - read + write
            else:
                cycles = 8  # Register operations

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
    
    def _check_interrupts(self) -> bool:
        """Check if any interrupts should be serviced. Returns True if interrupt was handled."""
        if not self.ime:
            return False

        # Read IE and IF registers
        ie = self.memory.read_byte(0xFFFF)  # Interrupt Enable
        if_flags = self.memory.read_byte(0xFF0F)  # Interrupt Flags

        # Check which interrupts are both enabled and requested
        triggered = ie & if_flags & 0x1F  # Only bits 0-4 are used

        if triggered == 0:
            return False

        self._service_interrupt()
        return True

    def _request_interrupt(self, interrupt_bit: int) -> None:
        """
        Request an interrupt by setting the appropriate bit in IF register

        Args:
            interrupt_bit: Which interrupt to request (0=VBlank, 1=STAT, 2=Timer, 3=Serial, 4=Joypad)
        """
        if_flags = self.memory.read_byte(0xFF0F)
        if_flags |= (1 << interrupt_bit)
        self.memory.write_byte(0xFF0F, if_flags)

    def _service_interrupt(self) -> None:
        """Dispatch the highest-priority pending interrupt.

        The CPU pushes PC's high byte first and only then decides which interrupt
        to run. If that push overwrote IE (SP was 0x0000) and nothing enabled is
        left, the dispatch is cancelled and execution continues at 0x0000.
        """
        self.ime = False
        self._ei_pending = 0
        self.halted = False

        pc = self.registers._pc
        self._acc += 8                      # two internal cycles
        sp = (self.registers._sp - 1) & 0xFFFF
        self._write(sp, pc >> 8)
        self._catch_up()
        triggered = self.memory.read_byte(0xFFFF) & self.memory.read_byte(0xFF0F) & 0x1F
        sp = (sp - 1) & 0xFFFF
        self._write(sp, pc & 0xFF)
        self.registers._sp = sp

        if not triggered:
            self.registers._pc = 0x0000
            return
        bit = (triggered & -triggered).bit_length() - 1     # lowest bit = highest priority
        self.memory.write_byte(0xFF0F, self.memory.read_byte(0xFF0F) & ~(1 << bit))
        self.registers._pc = 0x0040 + 8 * bit

    def _trigger_timer_tick(self) -> None:
        """
        Trigger a spurious timer tick (from TAC write obscure behavior).
        This increments TIMA and handles overflow.
        """
        tima = self.memory.read_byte(0xFF05)
        tima += 1

        if tima > 0xFF:
            # Overflow - set TIMA to 0 and start delay
            self.memory._data[0xFF05] = 0x00
            self._timer_overflow_cycles = 1
        else:
            self.memory._data[0xFF05] = tima

    def _update_timers(self, cycles: int) -> None:
        """
        Update timer registers with cycle-accurate behavior.

        The Game Boy has a 16-bit system counter that increments every T-cycle.
        - DIV is bits 13-6 of this counter (visible at 0xFF04)
        - TIMA increments on falling edge of a selected bit
        - TAC selects which bit: bit 9 (256 M-cycles), bit 3 (4 M-cycles), bit 5 (16 M-cycles), or bit 7 (64 M-cycles)
        """
        # Process each M-cycle individually for accuracy
        # Note: 1 M-cycle = 4 T-cycles
        for _ in range(cycles):
            if self._tima_reloaded:
                self._tima_reloaded = False
            # Handle timer overflow delay (1 M-cycle delay before TMA loads)
            if self._timer_overflow_cycles > 0:
                self._timer_overflow_cycles -= 1
                if self._timer_overflow_cycles == 0:
                    # Reload TIMA from TMA and request interrupt
                    tma = self.memory.read_byte(0xFF06)
                    self.memory._data[0xFF05] = tma
                    self._tima_reloaded = True

                    # Set timer interrupt flag
                    if_flags = self.memory.read_byte(0xFF0F)
                    if_flags |= 0x04
                    self.memory.write_byte(0xFF0F, if_flags)

            # Increment system counter (4 T-cycles per M-cycle)
            prev_counter = self._system_counter
            self._system_counter = (self._system_counter + 4) & 0xFFFF

            # Update DIV register (increments every 256 T-cycles)
            # System counter bits: [15:14][13:6][5:0]
            # DIV uses bits 13-6 of system counter
            # DIV = system_counter / 256
            self.memory._data[0xFF04] = (self._system_counter // 256) & 0xFF

            # Check if timer is enabled
            tac = self.memory.read_byte(0xFF07)
            if tac & 0x04:  # Bit 2 = timer enable
                # Select which bit to monitor based on TAC bits 0-1
                freq_bits = tac & 0x03
                # Bit positions: [9, 3, 5, 7] for frequencies [256, 4, 16, 64] M-cycles
                bit_positions = [9, 3, 5, 7]
                selected_bit_pos = bit_positions[freq_bits]

                # Get current and previous bit values
                prev_bit = (prev_counter >> selected_bit_pos) & 1
                curr_bit = (self._system_counter >> selected_bit_pos) & 1

                # Detect falling edge (1 -> 0 transition)
                if prev_bit == 1 and curr_bit == 0:
                    # Increment TIMA
                    tima = self.memory.read_byte(0xFF05)
                    tima += 1

                    if tima > 0xFF:
                        # Overflow detected - set TIMA to 0 and start delay
                        self.memory._data[0xFF05] = 0x00
                        self._timer_overflow_cycles = 1  # 1 M-cycle delay
                    else:
                        self.memory._data[0xFF05] = tima

    # --- bus timing -----------------------------------------------------------
    # Inside an instruction, self._acc counts the T-cycles of the M-cycles
    # started so far (fetches, reads, writes, internal delays) and
    # self._synced how far the timer, PPU and OAM DMA have been advanced.
    # Before an access that can observe them (I/O, VRAM, OAM, or anything
    # while DMA runs) they catch up to the start of that access's M-cycle;
    # the rest is advanced at the end of the instruction.

    def _advance(self, t: int) -> None:
        """Run the timer, PPU and OAM DMA for t T-cycles."""
        mem = self.memory
        if mem._dma_busy:
            for _ in range(t >> 2):
                self._update_timers(1)
                self.ppu.step(4)
                mem.dma_tick()
        else:
            self._update_timers(t >> 2)
            self.ppu.step(t)

    def _catch_up(self) -> None:
        t = self._acc - self._synced
        if t > 0:
            self._synced = self._acc
            self._advance(t)

    def _read(self, address: int) -> int:
        """CPU bus read: one M-cycle."""
        if 0xFE00 <= address < 0xFF80 or 0x8000 <= address < 0xA000 or self.memory._dma_busy:
            self._catch_up()
        self._acc += 4
        return self.memory.read_byte(address)

    def _write(self, address: int, value: int) -> None:
        """CPU bus write: one M-cycle."""
        if 0xFE00 <= address < 0xFF80 or 0x8000 <= address < 0xA000 or self.memory._dma_busy:
            self._catch_up()
        self._acc += 4
        self.memory.write_byte(address, value)

    def _idle_step(self) -> int:
        """Advance timer and PPU by one M-cycle without executing anything."""
        self._advance(4)
        self.total_cycles += 4
        return 4

    def step(self) -> int:
        """Execute one instruction"""
        if self.locked:
            return self._idle_step()

        if self.stopped:
            # A pressed button in the selected P1 group pulls a line low and wakes the CPU
            if self.memory.joypad.read_p1() & 0x0F != 0x0F:
                self.stopped = False
            else:
                self.ppu.step(4)
                self.total_cycles += 4
                return 4

        # If halted, update timers and PPU (so interrupt flags can be set)
        if self.halted:
            cycles = 4  # 4 T-cycles = 1 M-cycle
            self._advance(cycles)
            self.total_cycles += cycles

            # Then check if we should wake (after timers updated)
            ie = self.memory.read_byte(0xFFFF)
            if_flags = self.memory.read_byte(0xFF0F)
            if ie & if_flags & 0x1F:
                self.halted = False  # Wake from halt

            return cycles

        self._acc = 0
        self._synced = 0

        # Check for interrupts (only services them if IME=1)
        if self._check_interrupts():
            cycles = 20  # dispatch: 2 internal cycles, 2 pushes, 1 to set PC
            self._acc = cycles
            self._catch_up()
            self.total_cycles += cycles
            return cycles

        # FETCH
        opcode = self.fetch_byte()

        # Illegal opcodes hang the real CPU: it stops executing for good,
        # while the timer and PPU keep running.
        if opcode in ILLEGAL_OPCODES:
            self.locked = True
            print(f"CPU locked: illegal opcode 0x{opcode:02X} at 0x{(self.registers._pc - 1) & 0xFFFF:04X}")
            return self._idle_step()

        # DECODE
        instr_type, target, immediate, cycles = self.decode(opcode)

        # EXECUTE
        # Some instructions return actual cycles consumed (conditional branches)
        # If None is returned, use the cycles from decode
        actual_cycles = self.execute_instruction(instr_type, target, immediate)
        if actual_cycles is not None:
            cycles = actual_cycles

        # Handle EI delay: count down and enable interrupts when counter reaches 0
        # EI sets counter to 2, then: 2->1 (execute next instr), 1->0 (enable IME)
        if self._ei_pending > 0:
            self._ei_pending -= 1
            if self._ei_pending == 0:
                self.ime = True

        # Advance the timer, PPU and DMA through the rest of the instruction
        self._acc = cycles
        self._catch_up()

        self.total_cycles += cycles

        # Gameboy Doctor: Log current state after instruction execution
        if self._doctor_logger:
            self._doctor_logger.log_step(self)

        return cycles
    
    def run_until(self, max_cycles: int) -> None:
        """Run CPU for a specified number of cycles"""
        target_cycles = self.total_cycles + max_cycles
        while self.total_cycles < target_cycles:
            self.step()
            # Note: We continue stepping even when halted, because:
            # 1. Timers need to keep running while halted
            # 2. Interrupts can wake the CPU from HALT

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
            value = self._read(self.registers.hl)
        elif source == '(BC)':
            value = self._read(self.registers.bc)
        elif source == '(DE)':
            value = self._read(self.registers.de)
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
            self._write(self.registers.hl, validate_byte(value))
        elif target == '(BC)':
            self._write(self.registers.bc, validate_byte(value))
        elif target == '(DE)':
            self._write(self.registers.de, validate_byte(value))
        else:
            raise ValueError(f"Unknown LD target: {target}")
    
    # LD doesn't affect flags
    
    def _execute_add(self, target, immediate_value=None) -> None:
        """Execute ADD instruction"""
        # Use the helper function to get the operand value correctly
        value_to_add = self._get_operand_value(target, immediate_value)

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
        """
        Dispatch instruction to appropriate handler

        Returns:
            Optional[int]: Actual cycles consumed for instructions with variable timing
                          (conditional jumps/calls/returns). None means use default from opcode table.
        """
        # Most instructions return None (use default cycles from opcode table)
        # Only conditional control flow returns actual cycles

        if instr_type == InstructionType.NOP:
            pass

        elif instr_type == InstructionType.HALT:
            # Check for HALT bug: if IME=0 and interrupt is pending
            ie = self.memory.read_byte(0xFFFF)
            if_flags = self.memory.read_byte(0xFF0F)
            interrupt_pending = (ie & if_flags & 0x1F) != 0

            if not self.ime and interrupt_pending and self._ei_pending == 1:
                # EI right before HALT: IME turns on now, the interrupt is taken
                # and returns to the HALT itself, which then runs again.
                self.registers._pc = (self.registers._pc - 1) & 0xFFFF
            elif not self.ime and interrupt_pending:
                # HALT bug: halt exits immediately, PC fails to increment after next instruction
                # This causes the next instruction to be executed twice
                # Set flag to skip PC increment on the next fetch
                self._halt_bug_active = True
                # Don't enter halted state
            else:
                # Normal HALT: enter halted state
                self.halted = True

        elif instr_type == InstructionType.STOP:
            # DMG STOP: reset DIV and freeze CPU and timer until a button is pressed.
            # (KEY1 speed switching exists only on Game Boy Color.)
            self._system_counter = 0
            self.memory._data[0xFF04] = 0
            if self.memory.joypad.read_p1() & 0x0F == 0x0F:
                self.stopped = True

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

        # Control flow - these return actual cycles for conditional branches
        elif instr_type == InstructionType.JP:
            return self._execute_jp(target, immediate)

        elif instr_type == InstructionType.JP_HL:
            self._execute_jp_hl()

        elif instr_type == InstructionType.JR:
            return self._execute_jr(target, immediate)

        elif instr_type == InstructionType.CALL:
            return self._execute_call(target, immediate)

        elif instr_type == InstructionType.RET:
            return self._execute_ret(target)

        # Rotates/Shifts
        elif instr_type == InstructionType.RLCA:
            self._execute_rlca()

        elif instr_type == InstructionType.RLA:
            self._execute_rla()

        elif instr_type == InstructionType.RRCA:
            self._execute_rrca()

        elif instr_type == InstructionType.RRA:
            self._execute_rra()

        # 16-bit arithmetic
        elif instr_type == InstructionType.INC_16:
            self._execute_inc_16(target)

        elif instr_type == InstructionType.DEC_16:
            self._execute_dec_16(target)

        elif instr_type == InstructionType.ADD_HL:
            self._execute_add_hl(target)

        # More LD variants
        elif instr_type == InstructionType.LDI:
            self._execute_ldi(target, immediate)

        elif instr_type == InstructionType.LDD:
            self._execute_ldd(target, immediate)

        elif instr_type == InstructionType.LDH:
            self._execute_ldh(target, immediate)

        elif instr_type == InstructionType.LD_ADDR:
            self._execute_ld_addr(target, immediate)

        elif instr_type == InstructionType.LD_NN_SP:
            self._execute_ld_nn_sp(target)

        elif instr_type == InstructionType.ADD_SP_N:
            self._execute_add_sp_n(target)

        elif instr_type == InstructionType.LD_HL_SP_N:
            self._execute_ld_hl_sp_n(target)

        elif instr_type == InstructionType.LD_SP_HL:
            self._execute_ld_sp_hl()

        # ADC/SBC
        elif instr_type == InstructionType.ADC:
            self._execute_adc(target, immediate)

        elif instr_type == InstructionType.SBC:
            self._execute_sbc(target, immediate)

        # RETI/RST
        elif instr_type == InstructionType.RETI:
            self._execute_reti()

        elif instr_type == InstructionType.RST:
            self._execute_rst(target)

        # CB-prefixed instructions
        elif instr_type == InstructionType.RLC:
            self._execute_rlc(target)

        elif instr_type == InstructionType.RRC:
            self._execute_rrc(target)

        elif instr_type == InstructionType.RL:
            self._execute_rl(target)

        elif instr_type == InstructionType.RR:
            self._execute_rr(target)

        elif instr_type == InstructionType.SLA:
            self._execute_sla(target)

        elif instr_type == InstructionType.SRA:
            self._execute_sra(target)

        elif instr_type == InstructionType.SRL:
            self._execute_srl(target)

        elif instr_type == InstructionType.SWAP:
            self._execute_swap(target)

        elif instr_type == InstructionType.BIT:
            self._execute_bit(target, immediate)

        elif instr_type == InstructionType.RES:
            self._execute_res(target, immediate)

        elif instr_type == InstructionType.SET:
            self._execute_set(target, immediate)

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