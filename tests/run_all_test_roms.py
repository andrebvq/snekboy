"""
Run All Blargg Test ROMs

This script systematically runs all available Blargg test ROMs and reports results.

Usage:
    python tests/run_all_test_roms.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cpu import CPU

def run_test_rom(rom_path, max_cycles=20_000_000, timeout_is_fail=True):
    """
    Run a test ROM and return the result

    Returns:
        (status, output, cycles)
        status: 'PASS', 'FAIL', 'TIMEOUT', 'HALTED', 'ERROR'
    """
    if not os.path.exists(rom_path):
        return 'ERROR', f'ROM not found: {rom_path}', 0

    try:
        cpu = CPU()
        cpu.memory.load_rom_file(rom_path)

        while cpu.total_cycles < max_cycles:
            cpu.step()

            out = cpu.memory.get_serial_output()

            # Check for completion
            if 'Passed' in out:
                return 'PASS', out, cpu.total_cycles
            elif 'Failed' in out:
                return 'FAIL', out, cpu.total_cycles

            # Check if halted and stuck
            if cpu.halted:
                halt_start = cpu.total_cycles
                stuck = True
                while cpu.total_cycles < halt_start + 1_000_000:
                    cpu.step()
                    if not cpu.halted:
                        stuck = False
                        break
                if stuck:
                    out = cpu.memory.get_serial_output()
                    if 'Passed' in out:
                        return 'PASS', out, cpu.total_cycles
                    elif 'Failed' in out:
                        return 'FAIL', out, cpu.total_cycles
                    else:
                        return 'HALTED', out, cpu.total_cycles

        # Timeout
        out = cpu.memory.get_serial_output()
        if 'Passed' in out:
            return 'PASS', out, cpu.total_cycles
        elif 'Failed' in out:
            return 'FAIL', out, cpu.total_cycles
        else:
            status = 'TIMEOUT' if timeout_is_fail else 'TIMEOUT'
            return status, out, cpu.total_cycles

    except Exception as e:
        return 'ERROR', str(e), 0

def main():
    print('=' * 80)
    print('BLARGG TEST ROM SUITE')
    print('=' * 80)
    print()

    # Define test ROMs with their expected behavior
    test_roms = [
        # CPU instruction tests
        ('cpu_instrs.gb', 'CPU Instructions (all)', 60_000_000, False),
        ('03-op_sp_hl.gb', 'Test 03: OP SP,HL', 10_000_000, True),

        # Timing tests
        ('instr_timing/instr_timing.gb', 'Instruction Timing', 10_000_000, True),
        ('interrupt_time/interrupt_time.gb', 'Interrupt Timing', 20_000_000, False),

        # Memory timing
        ('mem_timing/mem_timing.gb', 'Memory Timing', 20_000_000, False),
        ('mem_timing-2/mem_timing.gb', 'Memory Timing 2', 20_000_000, False),

        # Special cases
        ('halt_bug.gb', 'HALT Bug', 30_000_000, False),
    ]

    results = []

    for rom_file, description, max_cycles, timeout_fail in test_roms:
        rom_path = os.path.join('test_roms', rom_file)

        print(f'Testing: {description}')
        print(f'  ROM: {rom_file}')

        status, output, cycles = run_test_rom(rom_path, max_cycles, timeout_fail)

        # Format result
        if status == 'PASS':
            result_str = '\033[92m[PASS]\033[0m' if sys.stdout.isatty() else '[PASS]'
        elif status == 'FAIL':
            result_str = '\033[91m[FAIL]\033[0m' if sys.stdout.isatty() else '[FAIL]'
        elif status == 'TIMEOUT':
            result_str = '\033[93m[TIMEOUT]\033[0m' if sys.stdout.isatty() else '[TIMEOUT]'
        elif status == 'HALTED':
            result_str = '\033[93m[HALTED]\033[0m' if sys.stdout.isatty() else '[HALTED]'
        else:
            result_str = '\033[91m[ERROR]\033[0m' if sys.stdout.isatty() else '[ERROR]'

        print(f'  Result: {result_str}')
        print(f'  Cycles: {cycles:,}')

        # Show relevant output
        if output.strip():
            lines = output.strip().split('\n')
            last_line = lines[-1] if lines else ''
            if last_line:
                # Truncate if too long
                if len(last_line) > 60:
                    last_line = last_line[:60] + '...'
                print(f'  Output: {last_line}')

        print()

        results.append((description, status, cycles))

    # Summary
    print('=' * 80)
    print('SUMMARY')
    print('=' * 80)

    passed = sum(1 for _, status, _ in results if status == 'PASS')
    failed = sum(1 for _, status, _ in results if status == 'FAIL')
    timeout = sum(1 for _, status, _ in results if status == 'TIMEOUT')
    other = sum(1 for _, status, _ in results if status not in ['PASS', 'FAIL', 'TIMEOUT'])
    total = len(results)

    print(f'Total tests: {total}')
    print(f'  Passed:  {passed}')
    print(f'  Failed:  {failed}')
    print(f'  Timeout: {timeout}')
    print(f'  Other:   {other}')
    print()

    if passed == total:
        print('All tests PASSED!')
        return 0
    else:
        print(f'{total - passed} test(s) did not pass.')
        return 1

if __name__ == '__main__':
    sys.exit(main())
