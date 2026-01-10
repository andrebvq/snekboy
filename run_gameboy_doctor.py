"""
Runner script for Gameboy Doctor tests

This script runs the emulator in Gameboy Doctor mode to generate execution logs
for debugging and validation.

Usage:
    python run_gameboy_doctor.py <rom_file> [max_cycles]

Example:
    python run_gameboy_doctor.py tests/roms/03-op_sp_hl.gb 1000000

Environment:
    Automatically sets GAMEBOY_DOCTOR=1
"""

import os
import sys

# Enable Gameboy Doctor mode
os.environ['GAMEBOY_DOCTOR'] = '1'

from src.cpu import CPU
from src.gameboy_doctor import initialize_cpu_for_doctor


def run_gameboy_doctor_test(rom_path, max_cycles=1_000_000, log_path="emulator_log.txt"):
    """
    Run a ROM in Gameboy Doctor mode

    Args:
        rom_path: Path to ROM file
        max_cycles: Maximum cycles to execute (default 1M)
        log_path: Path to output log file
    """
    print("=" * 70)
    print("GAMEBOY DOCTOR MODE")
    print("=" * 70)
    print(f"ROM:        {rom_path}")
    print(f"Max Cycles: {max_cycles:,}")
    print(f"Log File:   {log_path}")
    print("=" * 70)

    # Create CPU
    cpu = CPU()

    # Load ROM
    print(f"\nLoading ROM: {rom_path}")
    try:
        cpu.memory.load_rom_file(rom_path)
        print("ROM loaded successfully")
    except Exception as e:
        print(f"ERROR: Failed to load ROM: {e}")
        return False

    # Initialize CPU to Gameboy Doctor state
    initialize_cpu_for_doctor(cpu)

    # Print initial state
    print("\nInitial CPU state:")
    print(f"  A=0x{cpu.registers._a:02X} F=0x{cpu.registers.flags.zero << 7 | cpu.registers.flags.subtract << 6 | cpu.registers.flags.half_carry << 5 | cpu.registers.flags.carry << 4:02X}")
    print(f"  B=0x{cpu.registers._b:02X} C=0x{cpu.registers._c:02X}")
    print(f"  D=0x{cpu.registers._d:02X} E=0x{cpu.registers._e:02X}")
    print(f"  H=0x{cpu.registers._h:02X} L=0x{cpu.registers._l:02X}")
    print(f"  SP=0x{cpu.registers._sp:04X} PC=0x{cpu.registers._pc:04X}")

    # Log the initial state before executing any instructions
    # Gameboy Doctor expects the first log line to show the state at PC:0100 before execution
    if cpu._doctor_logger:
        print("\nLogging initial state before execution...")
        cpu._doctor_logger.log_step(cpu)

    # Run emulator
    print(f"\nRunning emulator for up to {max_cycles:,} cycles...")
    print("(Check serial output for test results)")
    print()

    cycles_executed = 0
    last_print = 0
    print_interval = 100_000

    try:
        while cycles_executed < max_cycles:
            cycles = cpu.step()
            cycles_executed += cycles

            # Print progress
            if cycles_executed - last_print >= print_interval:
                print(f"  Cycles: {cycles_executed:,} | PC: 0x{cpu.registers._pc:04X}")
                last_print = cycles_executed

                # Check for infinite loop (PC stuck)
                if cycles_executed > 500_000:
                    # Simple check: if serial output hasn't changed recently, might be done
                    pass

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nERROR: Emulator crashed: {e}")
        import traceback
        traceback.print_exc()

    print(f"\nCompleted {cycles_executed:,} cycles")
    print(f"Final PC: 0x{cpu.registers._pc:04X}")

    # Check serial output
    if cpu.memory._serial_output:
        print("\nSerial output:")
        serial_text = ''.join(chr(b) for b in cpu.memory._serial_output if 32 <= b <= 126)
        print(f"  {serial_text}")

    print(f"\nLog written to: {log_path}")
    print("\nTo compare with reference log, use Gameboy Doctor:")
    print(f"  gameboy-doctor {rom_path} {log_path}")
    print("=" * 70)

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_gameboy_doctor.py <rom_file> [max_cycles]")
        print()
        print("Examples:")
        print("  python run_gameboy_doctor.py tests/roms/03-op_sp_hl.gb")
        print("  python run_gameboy_doctor.py tests/roms/01-special.gb 2000000")
        sys.exit(1)

    rom_path = sys.argv[1]
    max_cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000

    success = run_gameboy_doctor_test(rom_path, max_cycles)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
