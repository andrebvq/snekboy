from src.registers import Register
from src.utils import validate_byte, validate_word
from src.memory import Memory
from src.opcodes import OPCODES, CB_OPCODES
from src.instructions_impl import InstructionImplementations
from src.cpu_decoder import InstructionType, decode_instruction_params, decode_cb_instruction
from src.ppu import PPU
from src import fast_ops
from src.gameboy_doctor import create_logger_if_enabled  # Gameboy Doctor integration

# Opcodes with no instruction on the SM83; executing one locks up the CPU.
ILLEGAL_OPCODES = frozenset({0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD})

class CPU(InstructionImplementations):
    def __init__(self, memory = None):
        self.registers = Register()
        self._build_dispatch()

        # Timer state - must be initialized before Memory
        # The Game Boy has an internal 16-bit counter that increments every T-cycle (M-cycle = 4 T-cycles)
        self._system_counter = 0  # Internal 16-bit counter
        self._prev_timer_bit = False  # Previous value of selected timer bit for edge detection
        self._timer_overflow_cycles = 0  # 1 while TIMA reads 0x00 after overflow, before the TMA reload
        self._tima_reloaded = False  # True if the most recent M-cycle reloaded TIMA from TMA
        self._serial_bits = 0  # bits left in an internally clocked serial transfer

        # Create memory with reference to this CPU
        self.memory = memory if memory else Memory(cpu=self)
        self.memory._cpu = self   # a Memory passed in must also reach the CPU's timer
        self.memory.joypad.interrupt_callback = self._request_interrupt

        # Create PPU with reference to memory and interrupt callback
        self.ppu = PPU(self.memory, self._request_interrupt)

        self.total_cycles = 0
        self.halted = False
        self.ime = False  # Interrupt Master Enable flag
        self._ei_pending = 0  # EI delay counter: counts down to 0 before enabling IME
        self._halt_bug_active = False  # HALT bug: skip next PC increment
        self._acc = 0      # T-cycles started in the current instruction
        self._synced = 0   # T-cycles the timer/PPU/DMA have been advanced to
        # Lazy sync (frame runner only, see run_until_cycle): cycles owed to the
        # timer/PPU from earlier instructions, and how many may be owed before
        # the next event that could raise an interrupt.
        self._lazy = False
        self._lag = 0
        self._budget = 0
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
            self.registers._pc = (self.registers._pc + 1) & 0xFFFF

        return value
    
    def fetch_word(self) -> int:
        """Fetch next word (16-bit) from memory at PC and increment PC"""
        pc = self.registers._pc
        value = self._read(pc) | (self._read((pc + 1) & 0xFFFF) << 8)
        self.registers._pc = (pc + 2) & 0xFFFF
        return value
    
    def _check_interrupts(self) -> bool:
        """Check if any interrupts should be serviced. Returns True if interrupt was handled."""
        if not self.ime:
            return False

        d = self.memory._data
        if not d[0xFFFF] & d[0xFF0F] & 0x1F:     # enabled and requested
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

    def _serial_shift(self) -> None:
        """Shift one bit out of SB; with nothing connected, 1s shift in."""
        d = self.memory._data
        d[0xFF01] = ((d[0xFF01] << 1) | 1) & 0xFF
        self._serial_bits -= 1
        if not self._serial_bits:
            d[0xFF02] &= 0x7F            # transfer done
            self._request_interrupt(3)

    def _update_timers(self, cycles: int) -> None:
        """Advance DIV/TIMA by `cycles` M-cycles.

        Fast path: with no overflow, reload or serial transfer in progress,
        TIMA ticks are counted arithmetically (one per multiple of the
        selected bit's period crossed). Anything that needs cycle-exact
        handling goes through _update_timers_exact.
        """
        if self._timer_overflow_cycles or self._tima_reloaded or self._serial_bits:
            self._update_timers_exact(cycles)
            return
        d = self.memory._data
        old = self._system_counter
        new = old + cycles * 4
        tac = d[0xFF07]
        if tac & 0x04:
            shift = (10, 4, 6, 8)[tac & 0x03]     # selected bit + 1
            edges = (new >> shift) - (old >> shift)
            if edges:
                tima = d[0xFF05] + edges
                if tima > 0xFF:                   # overflow inside this batch
                    self._update_timers_exact(cycles)
                    return
                d[0xFF05] = tima
        self._system_counter = new & 0xFFFF
        d[0xFF04] = (new >> 8) & 0xFF

    def _update_timers_exact(self, cycles: int) -> None:
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

            # Serial (internal clock, 8192 Hz): one bit per falling edge of counter bit 8
            if self._serial_bits and prev_counter & 0x100 and not self._system_counter & 0x100:
                self._serial_shift()

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
            self._budget -= t           # lazy sync: an event passed -> recompute
            if self._budget <= 0:
                self._budget = self._sync_budget()

    def _sync_budget(self) -> int:
        """T-cycles the timer/PPU may fall behind before something could raise
        an interrupt: up to the next PPU event or the TIMA overflow edge. Zero
        (sync after every instruction) while DMA, a serial transfer or a TIMA
        overflow/reload is in progress."""
        if (self.memory._dma_busy or self._serial_bits or self._timer_overflow_cycles
                or self._tima_reloaded):
            return 0
        budget = 1 << 30
        dots = self.ppu.dots_to_next_event()
        if dots is not None:
            budget = dots
        d = self.memory._data
        tac = d[0xFF07]
        if tac & 0x04:
            shift = (10, 4, 6, 8)[tac & 0x03]                 # selected bit + 1
            c = self._system_counter
            overflow_at = ((c >> shift) + 256 - d[0xFF05]) << shift
            budget = min(budget, ((overflow_at - c + 3) >> 2) << 2)
        return budget

    def _settle_owed(self) -> None:
        """Inside an instruction: pay back cycles owed from earlier
        instructions (a negative _synced), as if synced at its start."""
        if self._synced < 0:
            t = -self._synced
            self._synced = 0
            self._advance(t)
            self._budget = 0

    def _settle_lag(self) -> None:
        """Pay back cycles owed from earlier instructions (lazy sync)."""
        if self._lag:
            t = self._lag
            self._lag = 0
            self._advance(t)
            self._budget = 0

    def _read(self, address: int) -> int:
        """CPU bus read: one M-cycle."""
        mem = self.memory
        if not mem._dma_busy:
            # Fast path: cartridge ROM (past the boot ROM area), work RAM and
            # high RAM have no side effects and nothing to catch up with.
            if 0x0100 <= address < 0x8000 or 0xC000 <= address < 0xE000 or 0xFF80 <= address <= 0xFFFF:
                self._acc += 4
                return mem._data[address]
            if 0xFE00 <= address < 0xFF80 or 0x8000 <= address < 0xA000:
                self._catch_up()
        else:
            self._catch_up()
        self._acc += 4
        return mem.read_byte(address)

    def _write(self, address: int, value: int) -> None:
        """CPU bus write: one M-cycle."""
        if 0xFE00 <= address < 0xFF80 or 0x8000 <= address < 0xA000 or self.memory._dma_busy:
            self._catch_up()
            self._acc += 4
            self.memory.write_byte(address, value)
            if address >= 0xFF00:
                self._budget = 0        # timer/LCD registers may move the next event
            return
        self._acc += 4
        self.memory.write_byte(address, value)

    def _idle_step(self) -> int:
        """Advance timer and PPU by one M-cycle without executing anything."""
        self._advance(4)
        self._budget = 0
        self.total_cycles += 4
        return 4

    def step(self, deadline=None) -> int:
        """Execute one instruction (or one halted stretch).

        deadline: total_cycles value the caller runs to. When given, a halted
        CPU may skip ahead to the next event instead of idling one M-cycle per
        call (see _halt_skip); without it, behaviour is unchanged."""
        if self._lag and (self.locked or self.stopped or self.halted):
            self._settle_lag()

        if self.locked:
            return self._idle_step()

        if self.stopped:
            # A pressed button in the selected P1 group pulls a line low and wakes the CPU
            if self.memory.joypad.read_p1() & 0x0F != 0x0F:
                self.stopped = False
            else:
                self.ppu.step(4)
                self.total_cycles += 4
                self._budget = 0
                return 4

        # If halted, update timers and PPU (so interrupt flags can be set)
        if self.halted:
            m = self._halt_skip(deadline) if deadline is not None else 1
            cycles = 4 * m
            if self.memory._dma_busy:
                self._advance(cycles)
            else:                       # same as _advance, one call less
                self._update_timers(m)
                self.ppu.step(cycles)
            self.total_cycles += cycles
            self._budget = 0            # lazy sync: recompute after this stretch

            # Then check if we should wake (after timers updated)
            d = self.memory._data
            if d[0xFFFF] & d[0xFF0F] & 0x1F:
                self.halted = False  # Wake from halt

            return cycles

        # Cycles still owed from earlier instructions count as not yet synced,
        # so any catch-up in this instruction pays them back first.
        self._acc = 0
        self._synced = -self._lag
        self._lag = 0

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
            self._settle_owed()
            self.locked = True
            print(f"CPU locked: illegal opcode 0x{opcode:02X} at 0x{(self.registers._pc - 1) & 0xFFFF:04X}")
            return self._idle_step()

        # DECODE: table lookup, then fetch the operand (if any) into its slot
        fn, target, immediate, operand, slot, cycles = self._ops[opcode]
        if operand:
            if operand == 1:
                value = self.fetch_byte()
            elif operand == 2:
                value = self.fetch_word()
            elif operand == 4:                          # CB prefix
                fn, target, immediate, cycles = self._cb_ops[self.fetch_byte()]
                value = None
            else:                                       # STOP: padding byte
                self.fetch_byte()
                value = None
            if slot == 1:
                target = value
            elif slot == 2:
                immediate = value

        # EXECUTE: conditional control flow returns its actual cycle count
        actual_cycles = fn(target, immediate)
        if actual_cycles is not None:
            cycles = actual_cycles

        # Handle EI delay: count down and enable interrupts when counter reaches 0
        # EI sets counter to 2, then: 2->1 (execute next instr), 1->0 (enable IME)
        if self._ei_pending > 0:
            self._ei_pending -= 1
            if self._ei_pending == 0:
                self.ime = True

        # Advance the timer, PPU and DMA through the rest of the instruction.
        # In the frame runner this is deferred while no event can be reached.
        self._acc = cycles
        t = cycles - self._synced
        if self._lazy and t < self._budget:
            self._lag = t
        elif t > 0:
            self._synced = cycles
            self._advance(t)
            if self._lazy:
                self._budget -= t
                if self._budget <= 0:
                    self._budget = self._sync_budget()

        self.total_cycles += cycles

        # Gameboy Doctor: Log current state after instruction execution
        if self._doctor_logger:
            self._doctor_logger.log_step(self)

        return cycles
    
    def _halt_skip(self, deadline: int) -> int:
        """M-cycles a halted CPU can advance in one go with the same result as
        stepping one M-cycle at a time: up to the next PPU event, the M-cycle
        where TIMA overflows, or the deadline, whichever comes first. While
        DMA, a serial transfer or a TIMA reload is in progress, or an
        interrupt is already pending, it stays at 1."""
        d = self.memory._data
        if (self.memory._dma_busy or self._serial_bits or self._timer_overflow_cycles
                or self._tima_reloaded or d[0xFFFF] & d[0xFF0F] & 0x1F):
            return 1
        m = (deadline - self.total_cycles + 3) >> 2          # M-cycles left to the deadline
        dots = self.ppu.dots_to_next_event()
        if dots is not None:
            m = min(m, (dots + 3) >> 2)
        tac = d[0xFF07]
        if tac & 0x04:
            shift = (10, 4, 6, 8)[tac & 0x03]                 # selected bit + 1
            c = self._system_counter
            overflow_at = ((c >> shift) + 256 - d[0xFF05]) << shift
            m = min(m, (overflow_at - c + 3) >> 2)
        return m if m > 1 else 1

    def run_until_cycle(self, target: int) -> None:
        """Run until total_cycles reaches target (the usual frame loop).

        HALT may skip ahead without passing target, and the timer/PPU are only
        brought up to date when something could observe them: an I/O, VRAM or
        OAM access, an event that could raise an interrupt, or the end of the
        run. Everything is in sync again when this returns."""
        self._lazy = self._doctor_logger is None
        self._budget = 0
        try:
            while self.total_cycles < target:
                self.step(target)
        finally:
            self._settle_lag()
            self._lazy = False

    def run_until(self, max_cycles: int) -> None:
        """Run CPU for a specified number of cycles"""
        target_cycles = self.total_cycles + max_cycles
        while self.total_cycles < target_cycles:
            self.step()
            # Note: We continue stepping even when halted, because:
            # 1. Timers need to keep running while halted
            # 2. Interrupts can wake the CPU from HALT

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

    def _execute_halt(self) -> None:
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

    def _execute_stop(self) -> None:
        # DMG STOP: reset DIV and freeze CPU and timer until a button is pressed.
        # (KEY1 speed switching exists only on Game Boy Color.)
        self._settle_owed()                     # lazy sync: earlier instructions first
        self._system_counter = 0
        self.memory._data[0xFF04] = 0
        if self.memory.joypad.read_p1() & 0x0F == 0x0F:
            self.stopped = True

    def _handlers(self):
        """InstructionType -> handler(target, immediate). Returns the actual
        cycle count for variable-timing control flow, None otherwise."""
        T = InstructionType
        no_args = {
            T.NOP: lambda: None, T.HALT: self._execute_halt, T.STOP: self._execute_stop,
            T.SCF: self._execute_scf, T.CCF: self._execute_ccf, T.CPL: self._execute_cpl,
            T.DAA: self._execute_daa, T.DI: self._execute_di, T.EI: self._execute_ei,
            T.JP_HL: self._execute_jp_hl, T.RLCA: self._execute_rlca, T.RLA: self._execute_rla,
            T.RRCA: self._execute_rrca, T.RRA: self._execute_rra,
            T.LD_SP_HL: self._execute_ld_sp_hl, T.RETI: self._execute_reti,
        }
        target_only = {
            T.INC: self._execute_inc, T.DEC: self._execute_dec,
            T.PUSH: self._execute_push, T.POP: self._execute_pop,
            T.RET: self._execute_ret, T.INC_16: self._execute_inc_16,
            T.DEC_16: self._execute_dec_16, T.ADD_HL: self._execute_add_hl,
            T.LD_NN_SP: self._execute_ld_nn_sp, T.ADD_SP_N: self._execute_add_sp_n,
            T.LD_HL_SP_N: self._execute_ld_hl_sp_n, T.RST: self._execute_rst,
            T.RLC: self._execute_rlc, T.RRC: self._execute_rrc, T.RL: self._execute_rl,
            T.RR: self._execute_rr, T.SLA: self._execute_sla, T.SRA: self._execute_sra,
            T.SRL: self._execute_srl, T.SWAP: self._execute_swap,
        }
        both = {
            T.ADD: self._execute_add, T.SUB: self._execute_sub, T.AND: self._execute_and,
            T.OR: self._execute_or, T.XOR: self._execute_xor, T.CP: self._execute_cp,
            T.LD: self._execute_ld, T.JP: self._execute_jp, T.JR: self._execute_jr,
            T.CALL: self._execute_call, T.LDI: self._execute_ldi, T.LDD: self._execute_ldd,
            T.LDH: self._execute_ldh, T.LD_ADDR: self._execute_ld_addr,
            T.ADC: self._execute_adc, T.SBC: self._execute_sbc,
            T.BIT: self._execute_bit, T.RES: self._execute_res, T.SET: self._execute_set,
        }
        table = {t: (lambda f: lambda target, imm: f())(f) for t, f in no_args.items()}
        table.update({t: (lambda f: lambda target, imm: f(target))(f) for t, f in target_only.items()})
        table.update(both)
        return table

    def _build_dispatch(self) -> None:
        """Decode every opcode once, at start-up.

        The decoder is run with probe fetch functions that record which
        operand (none, byte or word) the opcode reads and where the decoded
        value goes (target or immediate). At run time step() only fetches
        that operand and drops it into the stored slot, giving exactly what
        decode_instruction_params would return, without re-decoding.

        Entry: (handler, target, immediate, operand, slot, cycles)
          operand: 0 none, 1 byte, 2 word, 3 byte discarded (STOP), 4 CB prefix
          slot:    0 none, 1 target, 2 immediate
        """
        handlers = self._handlers()
        probe = object()

        def decode(opcode, decoder):
            fetched = []
            def fetch_byte():
                fetched.append(1); return probe
            def fetch_word():
                fetched.append(2); return probe
            instr_type, target, imm = decoder(opcode, fetch_byte, fetch_word)
            operand = fetched[0] if fetched else 0
            slot = 1 if target is probe else 2 if imm is probe else 0
            if operand and not slot:
                operand = 3
            return handlers[instr_type], instr_type, target, imm, operand, slot

        types = {}                  # opcode or ('CB', cb) -> InstructionType, for tests/tools
        ops = [None] * 256
        for opcode, (name, length, cycles, flags) in OPCODES.items():
            if opcode in ILLEGAL_OPCODES or opcode == 0xCB:
                continue
            fn, types[opcode], target, imm, operand, slot = decode(opcode, decode_instruction_params)
            ops[opcode] = (fn, None if slot == 1 else target, None if slot == 2 else imm,
                           operand, slot, cycles)
        ops[0xCB] = (None, None, None, 4, 0, 0)

        cb_ops = [None] * 256
        for cb in range(256):
            fn, instr_type, target, imm, _, _ = decode(cb, lambda c, fb, fw: decode_cb_instruction(c))
            types[('CB', cb)] = instr_type
            if target == '(HL)':
                cycles = 12 if instr_type == InstructionType.BIT else 16
            else:
                cycles = 8
            cb_ops[cb] = (fn, target, imm, cycles)
        self._op_types = types

        # Swap in the dedicated handlers (src/fast_ops.py) for the frequent
        # opcodes. Operand kind, slot and cycles stay as decoded above; the
        # generic tables are kept so tests can compare the two.
        self._generic_ops, self._generic_cb_ops = list(ops), list(cb_ops)
        fast, fast_cb = fast_ops.build(self)
        for opcode, fn in fast.items():
            ops[opcode] = (fn,) + ops[opcode][1:]
        for cb, fn in fast_cb.items():
            cb_ops[cb] = (fn,) + cb_ops[cb][1:]
        self._ops = ops
        self._cb_ops = cb_ops

    def execute_instruction(self, instr_type, target, immediate):
        """Run one decoded instruction (kept for tools and tests). Returns
        the actual cycle count for conditional control flow, else None."""
        if not hasattr(self, '_handler_map'):
            self._handler_map = self._handlers()
        return self._handler_map[instr_type](target, immediate)

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