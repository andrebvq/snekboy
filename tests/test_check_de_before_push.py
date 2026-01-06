"""
Check what DE contains right before PUSH DE at 0x0861
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 03
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        break

# Run to just before PUSH DE
target_cycle = 12881056 - 4
while cpu.total_cycles < target_cycle:
    cpu.step()

# Now trace carefully
print("Tracing to PUSH DE at 0x0861...")
print("=" * 70)

while cpu.total_cycles < 12881100:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    if pc == 0x0861:
        print(f"\n[{cpu.total_cycles}] At PUSH DE (0x0861):")
        print(f"  DE = 0x{(cpu.registers._d << 8) | cpu.registers._e:04X}")
        print(f"  D = 0x{cpu.registers._d:02X}")
        print(f"  E = 0x{cpu.registers._e:02X}")
        print(f"  SP = 0x{cpu.registers._sp:04X}")

        # Check what's on stack before push
        print(f"\n  Stack before PUSH:")
        for i in range(8):
            addr = cpu.registers._sp - i
            val = cpu.memory.read_byte(addr)
            print(f"    [0x{addr:04X}] = 0x{val:02X}")

        cpu.step()

        # Check what was pushed
        print(f"\n  After PUSH:")
        print(f"  SP = 0x{cpu.registers._sp:04X}")
        print(f"  Pushed bytes:")
        print(f"    [0x{cpu.registers._sp:04X}] = 0x{cpu.memory.read_byte(cpu.registers._sp):02X}")
        print(f"    [0x{cpu.registers._sp+1:04X}] = 0x{cpu.memory.read_byte(cpu.registers._sp+1):02X}")

        break

    cpu.step()

print(f"{'='*70}")

# Now let's trace back - where did DE come from?
print("\nLet's find where DE was set...")
print(f"We need to trace back from cycle {cpu.total_cycles}")
print("\nLet me re-run and trace DE changes...")
print("=" * 70)

# Reset and rerun
cpu2 = CPU()
for i, byte in enumerate(rom_data):
    cpu2.memory._data[i] = byte

# Run to test 03
while cpu2.total_cycles < 12796300:
    cpu2.step()

# Trace DE from test 03 start to PUSH
de_history = []
while cpu2.total_cycles < 12881060:
    pc = cpu2.registers._pc
    de_before = (cpu2.registers._d << 8) | cpu2.registers._e

    cpu2.step()

    de_after = (cpu2.registers._d << 8) | cpu2.registers._e

    if de_after != de_before:
        de_history.append({
            'cycle': cpu2.total_cycles,
            'pc': pc,
            'de': de_after
        })

print(f"\nAll DE changes from test 03 start to PUSH:")
for entry in de_history[-50:]:  # Last 50
    marker = " <<<" if entry['de'] == 0x6000 else ""
    print(f"[{entry['cycle']:>10}] PC=0x{entry['pc']:04X} DE=0x{entry['de']:04X}{marker}")

print(f"{'='*70}")
