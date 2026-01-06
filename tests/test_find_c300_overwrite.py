"""
Find exactly when 0xC300 gets overwritten from success path to failure path
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 03
print("Running to test 03...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        print(f"Test 03 started at cycle {cpu.total_cycles:,}")
        break

# Check initial value at 0xC300
initial_c300 = cpu.memory.read_byte(0xC300)
print(f"Initial 0xC300 value: 0x{initial_c300:02X}\n")

# Monitor for changes
print("Monitoring 0xC300 for changes...")
print("=" * 70)

last_c300 = initial_c300
changes = []

while cpu.total_cycles < 20_000_000:
    pc_before = cpu.registers._pc
    c300_before = cpu.memory.read_byte(0xC300)

    cpu.step()

    c300_after = cpu.memory.read_byte(0xC300)

    if c300_after != c300_before:
        changes.append({
            'cycle': cpu.total_cycles,
            'pc': cpu.registers._pc,
            'pc_before': pc_before,
            'before': c300_before,
            'after': c300_after,
            'sp': cpu.registers._sp,
            'hl': cpu.registers.hl,
            'de': (cpu.registers._d << 8) | cpu.registers._e,
        })

        print(f"\n[{cpu.total_cycles:>10}] 0xC300 changed: 0x{c300_before:02X} -> 0x{c300_after:02X}")
        print(f"  PC before step: 0x{pc_before:04X}")
        print(f"  PC after step:  0x{cpu.registers._pc:04X}")
        print(f"  HL: 0x{cpu.registers.hl:04X}")
        print(f"  DE: 0x{(cpu.registers._d << 8) | cpu.registers._e:04X}")

        # Check if this is the critical change from 0x18 to 0xE0
        if c300_before == 0x18 and c300_after == 0xE0:
            print("\n" + "!" * 70)
            print("!!! CRITICAL: Success path (JR) overwritten with failure path (LDH) !!!")
            print("!" * 70)

            # Trace back to find what caused this
            print(f"\nLet's see what instruction wrote this...")
            print(f"PC before the write was at: 0x{pc_before:04X}")

            # Disassemble the instruction
            opcode = cpu.memory.read_byte(pc_before)
            print(f"Opcode: 0x{opcode:02X}")

            from src.opcodes import OPCODES
            if opcode in OPCODES:
                print(f"Instruction: {OPCODES[opcode][0]}")

            break

    if cpu.halted:
        print(f"\nCPU halted at {cpu.total_cycles:,}")
        break

print(f"\n{'='*70}")
print(f"Total changes to 0xC300: {len(changes)}")
print(f"\nAll changes:")
for i, change in enumerate(changes):
    print(f"{i+1}. Cycle {change['cycle']:,}: 0x{change['before']:02X} -> 0x{change['after']:02X} (PC was 0x{change['pc_before']:04X})")
print(f"{'='*70}")
