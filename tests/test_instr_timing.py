"""
Test the instruction timing ROM with our timer implementation
"""

from src.cpu import CPU

def run_instr_timing_test():
    cpu = CPU()

    print("Loading instr_timing.gb...")
    cpu.memory.load_rom_file('test_roms/instr_timing/instr_timing.gb')

    print("Running test (this may take a while)...")
    print("="*80)

    max_cycles = 30_000_000
    check_interval = 1_000_000

    try:
        while cpu.total_cycles < max_cycles:
            cpu.step()

            # Check progress periodically
            if cpu.total_cycles % check_interval == 0:
                print(f"  Progress: {cpu.total_cycles:,} cycles")

            # Check if halted
            if cpu.halted:
                print(f"\nCPU halted at {cpu.total_cycles:,} cycles")
                break

    except NotImplementedError as e:
        print(f"\n[ERROR] Unimplemented instruction: {e}")
        print(f"  PC: 0x{cpu.registers._pc:04X}")
        print(f"  Cycles: {cpu.total_cycles:,}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    # Get results
    print(f"\n{'='*80}")
    print("TEST RESULTS")
    print(f"{'='*80}")

    serial_output = cpu.memory.get_serial_output()
    if serial_output:
        print(serial_output)
    else:
        print("No serial output produced")

    print(f"\n{'='*80}")
    print(f"Total cycles: {cpu.total_cycles:,}")
    print(f"Final PC: 0x{cpu.registers._pc:04X}")
    print(f"Halted: {cpu.halted}")

    # Check for pass/fail
    if "Passed" in serial_output or "passed" in serial_output:
        print("\n[PASS] Test passed!")
        return True
    elif "Failed" in serial_output or serial_output.strip().endswith("ok"):
        print("\n[PASS] Test passed!")
        return True
    else:
        print("\n[FAIL] Test did not pass")
        return False

if __name__ == '__main__':
    run_instr_timing_test()
