"""
Run the test longer and see if it gets past the loops
"""

from src.cpu import CPU

cpu = CPU()
cpu.memory.load_rom_file('test_roms/halt_bug.gb')

print("Running test for 5M cycles...")

last_pc = 0
same_count = 0
last_check = 0

try:
    while cpu.total_cycles < 5_000_000:
        cpu.step()

        # Check every 10000 cycles
        if cpu.total_cycles - last_check > 10000:
            pc = cpu.registers._pc

            if pc == last_pc:
                same_count += 1
                if same_count > 50:
                    print(f"Stuck at PC=0x{pc:04X} after {cpu.total_cycles:,} cycles")
                    break
            else:
                if same_count > 0:
                    print(f"  Moved from PC=0x{last_pc:04X} to PC=0x{pc:04X} at cycle {cpu.total_cycles:,}")
                same_count = 0
                last_pc = pc

            last_check = cpu.total_cycles

except NotImplementedError as e:
    print(f"\n[ERROR] Unimplemented: {e}")
    print(f"  PC: 0x{cpu.registers._pc:04X}")
    print(f"  Cycles: {cpu.total_cycles:,}")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print(f"\n\nFinal PC: 0x{cpu.registers._pc:04X}")
print(f"Total cycles: {cpu.total_cycles:,}")
print(f"Halted: {cpu.halted}")

serial = cpu.memory.get_serial_output()
if serial:
    print(f"\nSerial output:\n{serial}")
else:
    print(f"\nNo serial output")
