"""
Run Blargg's test ROMs and check results

The test ROMs write results to serial output (memory address 0xFF01/0xFF02).
A proper implementation would capture serial output, but for now we can
check the screen buffer or run for a set number of cycles.
"""

from src.cpu import CPU
from src.memory import Memory

def run_test_rom(rom_path, max_cycles=10_000_000):
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
        print(f"✗ File not found: {rom_path}")
        print("  Run download_test_roms.py first")
        return False
    
    print(f"ROM loaded, running for {max_cycles:,} cycles...")
    
    try:
        cpu.run_until(max_cycles)
        print(f"✓ Completed {cpu.total_cycles:,} cycles without crashing")
        
        # TODO: Check serial output for "Passed" message
        # For now, just check it didn't crash
        return True
        
    except NotImplementedError as e:
        print(f"✗ Unimplemented instruction: {e}")
        print(f"  PC: 0x{cpu.registers._pc:04X}")
        print(f"  Cycles: {cpu.total_cycles:,}")
        return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
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
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {rom}")

if __name__ == '__main__':
    # Run individual test
    run_test_rom('test_roms/cpu_instrs.gb')
    
    # Or run all tests
    # run_all_tests()
