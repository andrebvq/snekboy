"""
Run Blargg timing tests

Tests CPU instruction timing and memory access timing
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

def run_test(rom_path, max_cycles=30_000_000, timeout_cycles=10_000_000):
    """
    Run a Blargg test ROM

    Args:
        rom_path: Path to test ROM
        max_cycles: Maximum cycles to run
        timeout_cycles: Consider hung if no serial output after this many cycles

    Returns:
        tuple: (passed, result_text)
    """
    print(f"\n{'='*70}")
    print(f"Running: {os.path.basename(rom_path)}")
    print(f"{'='*70}")

    cpu = CPU()

    try:
        cpu.memory.load_rom_file(rom_path)
    except Exception as e:
        return False, f"Failed to load ROM: {e}"

    cycles = 0
    last_serial_len = 0
    no_progress_cycles = 0

    while cycles < max_cycles:
        try:
            step_cycles = cpu.step()
            cycles += step_cycles

            # Check for serial output (test results)
            serial_len = len(cpu.memory._serial_output)
            if serial_len > last_serial_len:
                # Progress made
                last_serial_len = serial_len
                no_progress_cycles = 0
            else:
                no_progress_cycles += step_cycles

            # Check if hung (no serial output for a while)
            if no_progress_cycles > timeout_cycles:
                serial_text = ''.join(chr(b) for b in cpu.memory._serial_output if 32 <= b <= 126)
                if "Passed" in serial_text:
                    return True, serial_text
                elif "Failed" in serial_text:
                    return False, serial_text
                else:
                    return False, f"Test hung after {cycles:,} cycles. Output: {serial_text}"

            # Print progress every 1M cycles
            if cycles % 1_000_000 == 0:
                print(f"  {cycles//1_000_000}M cycles...", end='\r')

        except NotImplementedError as e:
            serial_text = ''.join(chr(b) for b in cpu.memory._serial_output if 32 <= b <= 126)
            return False, f"Unimplemented instruction at {cycles:,} cycles: {e}\nOutput: {serial_text}"

        except Exception as e:
            serial_text = ''.join(chr(b) for b in cpu.memory._serial_output if 32 <= b <= 126)
            return False, f"Error at {cycles:,} cycles: {e}\nOutput: {serial_text}"

    # Max cycles reached
    serial_text = ''.join(chr(b) for b in cpu.memory._serial_output if 32 <= b <= 126)
    if "Passed" in serial_text:
        return True, serial_text
    elif "Failed" in serial_text:
        return False, serial_text
    else:
        return False, f"Max cycles reached ({max_cycles:,}). Output: {serial_text}"


def main():
    """Run timing tests"""

    # Timing test ROMs to run
    tests = [
        "test_roms/instr_timing/instr_timing.gb",
        "test_roms/mem_timing/mem_timing.gb",
        "test_roms/mem_timing/individual/01-read_timing.gb",
        "test_roms/mem_timing/individual/02-write_timing.gb",
        "test_roms/mem_timing/individual/03-modify_timing.gb",
    ]

    results = []

    for test_rom in tests:
        if not os.path.exists(test_rom):
            print(f"\nSkipping {test_rom} (not found)")
            continue

        passed, output = run_test(test_rom)
        results.append((test_rom, passed, output))

        # Print result
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"\n{status}")
        print(f"Output: {output[:200]}")  # First 200 chars

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    for rom, passed, output in results:
        status = "✅" if passed else "❌"
        print(f"{status} {os.path.basename(rom)}")

    print(f"\n{passed_count}/{total_count} tests passed")

    return 0 if passed_count == total_count else 1


if __name__ == '__main__':
    sys.exit(main())
