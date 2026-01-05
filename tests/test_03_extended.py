"""
Run test 03 for extended time with progress monitoring
"""

from src.cpu import CPU

def run_extended_test():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Running test for up to 100M cycles with progress monitoring...")
    print("=" * 70)

    max_cycles = 100_000_000
    last_serial = ""
    last_progress_cycles = 0
    progress_interval = 10_000_000

    try:
        while cpu.total_cycles < max_cycles:
            # Run in chunks
            chunk_cycles = min(1_000_000, max_cycles - cpu.total_cycles)
            cpu.run_until(chunk_cycles)

            # Check serial output
            serial = cpu.memory.get_serial_output()
            if serial != last_serial:
                new_text = serial[len(last_serial):]
                print(f"[{cpu.total_cycles:>11,}] Serial: {repr(new_text)}")
                last_serial = serial

                # Check for completion
                if "Passed" in serial or "Failed" in serial:
                    print(f"\n[TEST COMPLETE at {cpu.total_cycles:,} cycles]")
                    break

                # Check if test 03 completed
                if re.search(r'03:[a-z]+', serial):
                    print(f"\n[TEST 03 COMPLETED at {cpu.total_cycles:,} cycles]")
                    break

            # Progress report
            if cpu.total_cycles - last_progress_cycles >= progress_interval:
                print(f"[{cpu.total_cycles:>11,}] Still running... PC=0x{cpu.registers._pc:04X} Halted={cpu.halted}")
                last_progress_cycles = cpu.total_cycles

            # Check if stuck
            if cpu.halted and cpu.total_cycles > 50_000_000:
                print(f"\n[STUCK] Halted at {cpu.total_cycles:,} cycles, giving up")
                break

        print(f"\n{'='*70}")
        print(f"Stopped at {cpu.total_cycles:,} cycles")
        print(f"Final PC: 0x{cpu.registers._pc:04X}")
        print(f"Halted: {cpu.halted}")

        serial = cpu.memory.get_serial_output()
        print(f"\n{'='*70}")
        print("SERIAL OUTPUT:")
        print(f"{'='*70}")
        print(serial)
        print(f"{'='*70}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import re
    run_extended_test()
