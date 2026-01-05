"""
Trace execution around when code is copied to 0xC300
to understand why failure path is chosen
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

print("Running until test 03 starts...")

# Run until test 03 starts
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if "03" in serial:
        print(f"Test 03 started at cycle {cpu.total_cycles:,}")
        break

# Now watch for the copy operation (should be around 0x0200-0x0210)
print("\nWatching for copy operation to 0xC300...")
print("=" * 70)

last_c300 = None
trace_enabled = False
trace_buffer = []

while cpu.total_cycles < 20_000_000:
    pc = cpu.registers._pc

    # Enable tracing when we're in the copy routine area
    if 0x01F0 <= pc <= 0x0220:
        trace_enabled = True
        hl = cpu.registers.hl
        de = (cpu.registers._d << 8) | cpu.registers._e
        bc = (cpu.registers._b << 8) | cpu.registers._c
        entry = f"[{cpu.total_cycles:>10}] PC=0x{pc:04X} HL=0x{hl:04X} DE=0x{de:04X} BC=0x{bc:04X}"
        trace_buffer.append(entry)
        if len(trace_buffer) > 100:
            trace_buffer.pop(0)
    else:
        if trace_enabled:
            # Just exited copy routine - print the trace
            print("\nCopy routine trace:")
            for entry in trace_buffer:
                print(entry)
            trace_buffer = []
            trace_enabled = False

    # Check if 0xC300 changed
    c300_val = cpu.memory.read_byte(0xC300)
    if c300_val != last_c300:
        print(f"\n[{cpu.total_cycles:>10}] 0xC300 changed: 0x{last_c300 or 0:02X} -> 0x{c300_val:02X}")
        print(f"  PC=0x{pc:04X}")
        print(f"  HL=0x{cpu.registers.hl:04X} (source pointer during copy)")

        # Print a few bytes from the source
        if cpu.registers.hl < 0x8000:
            source_bytes = [cpu.memory.read_byte(cpu.registers.hl + i) for i in range(-4, 8)]
            print(f"  Source at HL-4: {' '.join(f'{b:02X}' for b in source_bytes)}")

        last_c300 = c300_val

        # If we're writing the failure path, stop and analyze
        if c300_val == 0xE0:  # First byte of failure path
            print("\n!!! FAILURE PATH being copied !!!")
            print("This means a test failed before reaching 0xC300")
            break

    cpu.step()

print(f"\n{'='*70}")
print(f"Stopped at {cpu.total_cycles:,} cycles")
