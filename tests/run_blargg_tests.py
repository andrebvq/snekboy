"""
Blargg Test ROM Suite

Run Blargg cpu_instrs test ROMs to verify CPU correctness.

Usage:
  python tests/run_blargg_tests.py           # Run main test suite
  python tests/run_blargg_tests.py debug     # Run with extra debugging
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cpu import CPU

def run_blargg_test(rom_path, max_cycles=30_000_000, debug=False):
    """Run a Blargg test ROM and return results"""
    if not os.path.exists(rom_path):
        return None, f"ROM not found: {rom_path}"

    cpu = CPU()
    cpu.memory.load_rom_file(rom_path)

    print(f"Running: {os.path.basename(rom_path)}")
    print(f"Max cycles: {max_cycles:,}")

    serial_output = []

    while cpu.total_cycles < max_cycles:
        cpu.step()

        # Check for serial output
        sc = cpu.memory.read_byte(0xFF02)
        if sc == 0x81:
            char = chr(cpu.memory.read_byte(0xFF01))
            serial_output.append(char)
            cpu.memory.write_byte(0xFF02, 0x00)

            if debug:
                print(char, end='', flush=True)

        # Check if halted (test complete)
        if cpu.halted:
            # Give it a bit more time in case it wakes up
            halt_cycles = cpu.total_cycles
            while cpu.total_cycles < halt_cycles + 100_000:
                cpu.step()
                if not cpu.halted:
                    break

            if cpu.halted:
                break

    output_str = ''.join(serial_output)

    return output_str, None

def main():
    debug = len(sys.argv) > 1 and sys.argv[1] == "debug"

    print("="*70)
    print("BLARGG CPU INSTRUCTION TESTS")
    print("="*70)
    print()

    test_rom = "test_roms/cpu_instrs.gb"

    if not os.path.exists(test_rom):
        print(f"ERROR: Test ROM not found: {test_rom}")
        print()
        print("Download test ROMs with:")
        print("  python tests/download_test_roms.py")
        sys.exit(1)

    output, error = run_blargg_test(test_rom, debug=debug)

    if error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print()
    print("="*70)
    print("SERIAL OUTPUT:")
    print("="*70)
    print(output)
    print("="*70)
    print()

    # Parse results
    if "Passed" in output or output.count(":ok") >= 2:
        print("RESULT: Tests PASSING")
        sys.exit(0)
    elif output.strip():
        print("RESULT: Tests INCOMPLETE or FAILING")
        print()
        print("Check output above for error codes.")
        print("See DEBUGGING_SESSION.md for known issues.")
        sys.exit(1)
    else:
        print("RESULT: No output (emulator may have crashed)")
        sys.exit(1)

if __name__ == "__main__":
    main()
