"""
Run Blargg's test ROMs and check results

The test ROMs write results to serial output (memory address 0xFF01/0xFF02).
A proper implementation would capture serial output, but for now we can
check the screen buffer or run for a set number of cycles.
"""

from src.cpu import CPU
from src.memory import Memory

def run_test_rom(rom_path, max_cycles=30_000_000, debug=False):
    """
    Run a test ROM and check for pass/fail

    Note: Full implementation requires serial port emulation
    For now, just verify it doesn't crash
    """
    print(f"\n{'='*50}")
    print(f"Running: {rom_path}")
    print(f"{'='*50}")

    cpu = CPU()

    try:
        cpu.memory.load_rom_file(rom_path)
    except FileNotFoundError:
        print(f"[FAIL] File not found: {rom_path}")
        print("  Run download_test_roms.py first")
        return False

    print(f"ROM loaded, running for {max_cycles:,} cycles...")

    if debug:
        last_pc = 0
        same_pc_count = 0
    
    try:
        cpu.run_until(max_cycles)
        print(f"\n[DONE] Completed {cpu.total_cycles:,} cycles")
        print(f"  Final PC: 0x{cpu.registers._pc:04X}")
        print(f"  Halted: {cpu.halted}")

        # Get full serial output
        serial_output = cpu.memory.get_serial_output()
        print(f"\n{'='*50}")
        print("SERIAL OUTPUT:")
        print(f"{'='*50}")
        print(serial_output)
        print(f"{'='*50}")

        # Check if test passed
        if "Passed" in serial_output:
            print("\n[PASS] Test passed!")
            return True
        elif "Failed" in serial_output:
            print("\n[FAIL] Test failed - check output above")
            return False
        else:
            print("\n[UNKNOWN] Test completed but result unclear")
            return False

    except NotImplementedError as e:
        print(f"[FAIL] Unimplemented instruction: {e}")
        print(f"  PC: 0x{cpu.registers._pc:04X}")
        print(f"  Cycles: {cpu.total_cycles:,}")
        return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all available test ROMs"""
    test_roms = [
        'test_roms/cpu_instrs.gb',
        'test_roms/instr_timing.gb',
    ]
    
    results = {}
    for rom in test_roms:
        results[rom] = run_test_rom(rom)
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for rom, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {rom}")

if __name__ == '__main__':
    # Run individual test
    run_test_rom('test_roms/cpu_instrs.gb')
    
    # Or run all tests
    # run_all_tests()
