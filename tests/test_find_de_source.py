"""
Find where DE gets its value (0x5300 or 0x6000) that determines success/failure
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

# Trace DE changes looking for when it gets set to 0x60xx or 0x53xx
print("Tracing for when DE gets loaded with path selector value...")
print("=" * 70)

last_de = (cpu.registers._d << 8) | cpu.registers._e

while cpu.total_cycles < 12882000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    d_before = cpu.registers._d
    e_before = cpu.registers._e
    de_before = (d_before << 8) | e_before

    cpu.step()

    d_after = cpu.registers._d
    e_after = cpu.registers._e
    de_after = (d_after << 8) | e_after

    # Check if D got set to 0x60 or 0x53
    if d_after != d_before:
        if d_after == 0x60 or d_after == 0x53:
            instr_name = OPCODES[opcode][0] if opcode in OPCODES else f"0x{opcode:02X}"
            print(f"\n[{cpu.total_cycles:>10}] PC=0x{pc:04X} {instr_name:15s} DE: 0x{de_before:04X} -> 0x{de_after:04X}")
            print(f"  A=0x{cpu.registers._a:02X}, Flags=0x{cpu.registers.flags._bits.value:02X}")

            if d_after == 0x60:
                print("  ^^^ D set to 0x60 (FAILURE PATH)!")

                # Dis assembly around this location
                print(f"\n  Disassembling around 0x{pc:04X}:")
                for offset in range(-10, 20):
                    addr = pc + offset
                    if 0 <= addr < 0x8000:
                        op = cpu.memory.read_byte(addr)
                        marker = " <--" if offset == 0 else ""
                        if op in OPCODES:
                            name = OPCODES[op][0]
                            print(f"    0x{addr:04X}: {name:20s}{marker}")

                # Show what's in memory at the addresses being loaded
                if instr_name.startswith("LD"):
                    print(f"\n  Checking memory/register sources...")
                    print(f"  A=0x{cpu.registers._a:02X}, B=0x{cpu.registers._b:02X}, C=0x{cpu.registers._c:02X}")
                    print(f"  HL=0x{cpu.registers.hl:04X}")

                break
            elif d_after == 0x53:
                print("  ^^^ D set to 0x53 (SUCCESS PATH)!")

print(f"\n{'='*70}")
