"""
Trace how DE is set to determine success vs failure path
"""

from src.cpu import CPU
from src.opcodes import OPCODES

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
        print(f"Test 03 started at cycle {cpu.total_cycles:,}\n")
        break

# Trace DE changes
print("Tracing DE register changes...")
print("=" * 70)

last_de = (cpu.registers._d << 8) | cpu.registers._e
de_changes = []

while cpu.total_cycles < 13_000_000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    d_before = cpu.registers._d
    e_before = cpu.registers._e
    de_before = (d_before << 8) | e_before

    cpu.step()

    d_after = cpu.registers._d
    e_after = cpu.registers._e
    de_after = (d_after << 8) | e_after

    if de_after != de_before:
        instr_name = OPCODES[opcode][0] if opcode in OPCODES else f"0x{opcode:02X}"

        de_changes.append({
            'cycle': cpu.total_cycles,
            'pc': pc,
            'opcode': opcode,
            'instr': instr_name,
            'de_before': de_before,
            'de_after': de_after,
            'a': cpu.registers._a,
            'flags': cpu.registers.flags._bits.value
        })

        # Print changes that set DE to 0x60xx or 0x53xx
        if (de_after & 0xFF00) == 0x6000 or (de_after & 0xFF00) == 0x5300:
            print(f"[{cpu.total_cycles:>10}] PC=0x{pc:04X} {instr_name:15s} DE: 0x{de_before:04X} -> 0x{de_after:04X}")

            if de_after == 0x6000:
                print("  ^^^ DE set to 0x6000 (FAILURE PATH)!")
                print(f"  A=0x{cpu.registers._a:02X}, Flags=0x{cpu.registers.flags._bits.value:02X}")
            elif de_after == 0x5300:
                print("  ^^^ DE set to 0x5300 (SUCCESS PATH)!")

    # Stop when HL is set from DE
    if pc == 0x0669:  # LD H,D
        print(f"\n{'='*70}")
        print(f"Reached LD H,D at cycle {cpu.total_cycles}")
        print(f"DE = 0x{(cpu.registers._d << 8) | cpu.registers._e:04X}")
        break

# Print last changes
print(f"\n{'='*70}")
print(f"Last 30 DE changes:")
print(f"{'='*70}")
for change in de_changes[-30:]:
    marker = ""
    if change['de_after'] == 0x6000:
        marker = " <<< FAILURE"
    elif change['de_after'] == 0x5300:
        marker = " <<< SUCCESS"

    print(f"[{change['cycle']:>10}] PC=0x{change['pc']:04X} {change['instr']:15s} DE: 0x{change['de_before']:04X} -> 0x{change['de_after']:04X}{marker}")

# Find the instruction that sets D to 0x60 (failure) instead of 0x53 (success)
print(f"\n{'='*70}")
print("Looking for where D gets set to 0x60...")
print(f"{'='*70}")
for change in de_changes:
    new_d = (change['de_after'] >> 8) & 0xFF
    old_d = (change['de_before'] >> 8) & 0xFF
    if new_d == 0x60 and old_d != 0x60:
        print(f"\nFound it!")
        print(f"  Cycle: {change['cycle']:,}")
        print(f"  PC: 0x{change['pc']:04X}")
        print(f"  Instruction: {change['instr']}")
        print(f"  DE: 0x{change['de_before']:04X} -> 0x{change['de_after']:04X}")
        print(f"  A: 0x{change['a']:02X}")
        print(f"  Flags: 0x{change['flags']:02X}")
        break
