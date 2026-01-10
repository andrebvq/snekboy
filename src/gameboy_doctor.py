"""
Gameboy Doctor integration for CPU trace logging and debugging.

This module provides logging functionality to generate execution traces
compatible with Gameboy Doctor for debugging and validation.

To enable: Set environment variable GAMEBOY_DOCTOR=1
To disable: Unset the variable or set to 0

All Gameboy Doctor-specific logic is contained in this file for easy removal.
"""

import os


class GameboyDoctorLogger:
    """Logger for Gameboy Doctor CPU trace output"""

    def __init__(self, log_file_path="emulator_log.txt"):
        """
        Initialize the logger

        Args:
            log_file_path: Path to the log file
        """
        self.log_file_path = log_file_path
        self.log_file = None
        self.enabled = True

        # Clear the log file on initialization
        try:
            with open(self.log_file_path, 'w') as f:
                f.write("")  # Clear file
            print(f"[Gameboy Doctor] Logging enabled, writing to {self.log_file_path}")
        except IOError as e:
            print(f"[Gameboy Doctor] Warning: Could not create log file: {e}")
            self.enabled = False

    def log_step(self, cpu):
        """
        Log CPU state in Gameboy Doctor format

        Format: A:01 F:B0 B:00 C:13 D:00 E:D8 H:01 L:4D SP:FFFE PC:0100 PCMEM:00,00,00,00

        Logs the current state of the CPU after instruction execution.
        PC shows where the CPU is now (ready to fetch next instruction).
        PCMEM shows the bytes at the current PC location.

        Args:
            cpu: CPU instance with registers and memory
        """
        if not self.enabled:
            return

        try:
            # Get register values (current state)
            a = cpu.registers._a
            b = cpu.registers._b
            c = cpu.registers._c
            d = cpu.registers._d
            e = cpu.registers._e
            h = cpu.registers._h
            l = cpu.registers._l
            sp = cpu.registers._sp
            pc = cpu.registers._pc  # Current PC

            # Get F register from flags
            f = self._get_f_register(cpu.registers.flags)

            # Get next 4 bytes at current PC for PCMEM
            pc_mem = []
            for i in range(4):
                addr = (pc + i) & 0xFFFF  # Wrap around at 64KB
                pc_mem.append(cpu.memory.read_byte(addr))
            pc_mem_str = ",".join(f"{b:02X}" for b in pc_mem)

            # Format log line
            log_line = (
                f"A:{a:02X} F:{f:02X} B:{b:02X} C:{c:02X} "
                f"D:{d:02X} E:{e:02X} H:{h:02X} L:{l:02X} "
                f"SP:{sp:04X} PC:{pc:04X} PCMEM:{pc_mem_str}\n"
            )

            # Write to file
            with open(self.log_file_path, 'a') as f:
                f.write(log_line)

        except Exception as e:
            # Don't crash the emulator if logging fails
            print(f"[Gameboy Doctor] Logging error: {e}")
            self.enabled = False

    @staticmethod
    def _get_f_register(flags):
        """
        Convert Flags object to F register byte

        F register format:
        Bit 7: Zero flag (Z)
        Bit 6: Subtract flag (N)
        Bit 5: Half-carry flag (H)
        Bit 4: Carry flag (C)
        Bits 3-0: Always 0

        Args:
            flags: Flags object with zero, subtract, half_carry, carry attributes

        Returns:
            int: F register value (0x00-0xFF)
        """
        f = 0
        if flags.zero:
            f |= 0x80  # Bit 7
        if flags.subtract:
            f |= 0x40  # Bit 6
        if flags.half_carry:
            f |= 0x20  # Bit 5
        if flags.carry:
            f |= 0x10  # Bit 4
        return f

    def close(self):
        """Close the log file"""
        if self.log_file:
            self.log_file.close()
            self.log_file = None


def is_gameboy_doctor_enabled():
    """
    Check if Gameboy Doctor mode is enabled via environment variable

    Returns:
        bool: True if GAMEBOY_DOCTOR=1, False otherwise
    """
    return os.environ.get('GAMEBOY_DOCTOR', '0') == '1'


def create_logger_if_enabled():
    """
    Create a GameboyDoctorLogger if enabled, otherwise return None

    Returns:
        GameboyDoctorLogger or None
    """
    if is_gameboy_doctor_enabled():
        return GameboyDoctorLogger()
    return None


def initialize_cpu_for_doctor(cpu):
    """
    Initialize CPU to Gameboy Doctor test state

    Sets registers to post-boot ROM state expected by Blargg tests:
    A=0x01, F=0xB0, B=0x00, C=0x13, D=0x00, E=0xD8, H=0x01, L=0x4D
    SP=0xFFFE, PC=0x0100

    Args:
        cpu: CPU instance to initialize
    """
    print("[Gameboy Doctor] Initializing CPU to test state")

    # Set registers
    cpu.registers._a = 0x01
    cpu.registers._b = 0x00
    cpu.registers._c = 0x13
    cpu.registers._d = 0x00
    cpu.registers._e = 0xD8
    cpu.registers._h = 0x01
    cpu.registers._l = 0x4D
    cpu.registers._sp = 0xFFFE
    cpu.registers._pc = 0x0100

    # Set flags from F=0xB0
    # 0xB0 = 0b10110000 = Z=1, N=0, H=1, C=1
    cpu.registers.flags.zero = True      # Bit 7
    cpu.registers.flags.subtract = False # Bit 6
    cpu.registers.flags.half_carry = True # Bit 5
    cpu.registers.flags.carry = True     # Bit 4


def should_override_ly_register():
    """
    Check if LY register should be overridden to 0x90 (VBlank)

    Returns:
        bool: True if Gameboy Doctor mode is enabled
    """
    return is_gameboy_doctor_enabled()


def get_overridden_ly_value():
    """
    Get the LY register override value for Gameboy Doctor mode

    Returns:
        int: 0x90 (VBlank line to avoid timing issues)
    """
    return 0x90
