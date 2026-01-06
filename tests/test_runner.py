"""
Test runner for Blargg test ROMs
Runs multiple test ROMs and reports results
"""

from src.cpu import CPU
import sys

def run_test_rom(rom_path, max_cycles=30_000_000, timeout_detection=True):
    """
    Run a test ROM and check for pass/fail

    Args:
        rom_path: Path to the test ROM
        max_cycles: Maximum cycles to run
        timeout_detection: Enable infinite loop detection

    Returns:
        (passed, serial_output, error_msg)
    """
    print(f"\n{'='*70}")
    print(f"Running: {rom_path}")
    print(f"{'='*70}")

    cpu = CPU()

    try:
        cpu.memory.load_rom_file(rom_path)
    except FileNotFoundError:
        return False, "", f"File not found: {rom_path}"

    print(f"ROM loaded, running for up to {max_cycles:,} cycles...")

    # Track PC for infinite loop detection
    last_pc = 0
    same_pc_count = 0
    last_cycle_count = 0

    try:
        while cpu.total_cycles < max_cycles:
            # Check for infinite loop (PC hasn't changed in 1000 cycles)
            if timeout_detection and cpu.total_cycles - last_cycle_count > 1000:
                if cpu.registers._pc == last_pc:
                    same_pc_count += 1
                    if same_pc_count > 10:
                        print(f"\n[TIMEOUT] Infinite loop detected at PC=0x{cpu.registers._pc:04X}")
                        break
                else:
                    same_pc_count = 0
                    last_pc = cpu.registers._pc
                last_cycle_count = cpu.total_cycles

            cpu.step()

            # Check if test has completed (HALT or infinite loop at specific address)
            if cpu.halted:
                print(f"\n[HALTED] CPU halted at {cpu.total_cycles:,} cycles")
                break

        print(f"\n[DONE] Completed {cpu.total_cycles:,} cycles")
        print(f"  Final PC: 0x{cpu.registers._pc:04X}")
        print(f"  Halted: {cpu.halted}")

        # Get serial output
        serial_output = cpu.memory.get_serial_output()

        if serial_output:
            print(f"\n{'='*70}")
            print("SERIAL OUTPUT:")
            print(f"{'='*70}")
            print(serial_output)
            print(f"{'='*70}")

        # Check if test passed
        if "Passed" in serial_output or "passed" in serial_output:
            print("\n[PASS] Test passed!")
            return True, serial_output, None
        elif "Failed" in serial_output or "failed" in serial_output:
            print("\n[FAIL] Test failed - check output above")
            return False, serial_output, "Test reported failure"
        else:
            print("\n[UNKNOWN] Test completed but result unclear")
            return False, serial_output, "No clear pass/fail in output"

    except NotImplementedError as e:
        error_msg = f"Unimplemented instruction: {e}"
        print(f"\n[FAIL] {error_msg}")
        print(f"  PC: 0x{cpu.registers._pc:04X}")
        print(f"  Cycles: {cpu.total_cycles:,}")

        serial_output = cpu.memory.get_serial_output()
        if serial_output:
            print(f"\nSerial output so far:\n{serial_output}")

        return False, serial_output, error_msg

    except Exception as e:
        error_msg = f"Error: {e}"
        print(f"\n[FAIL] {error_msg}")
        import traceback
        traceback.print_exc()

        serial_output = cpu.memory.get_serial_output()
        return False, serial_output, error_msg

def main():
    """Run test suite"""

    # Test suite in priority order
    test_suite = [
        # Priority 1: CPU instruction correctness
        {
            'name': 'HALT Bug Test',
            'path': 'test_roms/halt_bug.gb',
            'max_cycles': 10_000_000,
            'description': 'Tests HALT instruction behavior and bug'
        },
        {
            'name': 'CPU Instructions (Full)',
            'path': 'test_roms/cpu_instrs.gb',
            'max_cycles': 50_000_000,
            'description': 'Comprehensive CPU instruction test (tests 01-11)'
        },
        # Priority 2: Timing tests (may fail due to timing, not instruction bugs)
        {
            'name': 'Instruction Timing',
            'path': 'test_roms/instr_timing.gb',
            'max_cycles': 30_000_000,
            'description': 'Tests cycle timing of all instructions (requires timer)'
        },
        {
            'name': 'Interrupt Timing',
            'path': 'test_roms/interrupt_time.gb',
            'max_cycles': 20_000_000,
            'description': 'Tests interrupt timing (requires timer + interrupts)'
        },
    ]

    print("="*70)
    print("BLARGG TEST ROM SUITE")
    print("="*70)
    print(f"Running {len(test_suite)} tests...")

    results = []

    for test in test_suite:
        passed, output, error = run_test_rom(
            test['path'],
            max_cycles=test['max_cycles']
        )

        results.append({
            'name': test['name'],
            'path': test['path'],
            'passed': passed,
            'error': error,
            'output': output
        })

    # Print summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")

    passed_count = 0
    failed_count = 0

    for result in results:
        if result['passed']:
            status = "[PASS]"
            passed_count += 1
        else:
            status = "[FAIL]"
            failed_count += 1

        print(f"{status}: {result['name']}")
        if result['error']:
            print(f"         {result['error']}")

    print(f"\n{'='*70}")
    print(f"Results: {passed_count} passed, {failed_count} failed")
    print(f"{'='*70}")

    return failed_count == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
