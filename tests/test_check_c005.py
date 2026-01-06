"""
Check what's at the final PC location after test 03
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run until test 03 area
print("Running to test 03 completion point...")
while cpu.total_cycles < 14_000_000:
    cpu.step()
    if cpu.registers._pc == 0xC005:
        break

print(f"\nReached 0xC005 at cycle {cpu.total_cycles:,}")
print(f"Serial: {repr(cpu.memory.get_serial_output())}")

# Disassemble around 0xC000
print("\nDisassembling around 0xC000-0xC020:")
print("=" * 70)

addr = 0xBFF0
while addr < 0xC030:
    opcode = cpu.memory.read_byte(addr)
    marker = " <-- PC" if addr == cpu.registers._pc else ""

    if opcode in OPCODES:
        name, length, cycles, flags = OPCODES[opcode]
        hex_bytes = " ".join([f"{cpu.memory.read_byte(addr+i):02X}" for i in range(length)])
        operands = [cpu.memory.read_byte(addr + i) for i in range(1, length)]
        operand_str = ",".join([f"0x{op:02X}" for op in operands]) if operands else ""
        print(f"0x{addr:04X}:  {hex_bytes:12s}  {name:20s} {operand_str}{marker}")
        addr += length
    elif opcode == 0xCB:
        cb_op = cpu.memory.read_byte(addr + 1)
        print(f"0x{addr:04X}:  CB {cb_op:02X}         CB PREFIX{marker}")
        addr += 2
    else:
        print(f"0x{addr:04X}:  {opcode:02X}            [UNKNOWN]{marker}")
        addr += 1

# Check what happens if we continue
print(f"\n{'='*70}")
print("Continuing execution for 5M more cycles...")
last_pc = cpu.registers._pc
pc_history = []

for _ in range(5_000_000):
    pc = cpu.registers._pc
    if pc != last_pc:
        pc_history.append(pc)
        if len(pc_history) > 20:
            pc_history.pop(0)
        last_pc = pc

    cpu.step()

    serial = cpu.memory.get_serial_output()
    if ":ok" in serial or ("03:" in serial and "03" in serial):
        print(f"\nSerial updated at cycle {cpu.total_cycles:,}: {repr(serial)}")
        break

    if cpu.halted:
        print(f"\nHalted at cycle {cpu.total_cycles:,}, PC=0x{cpu.registers._pc:04X}")
        break

print(f"\n{'='*70}")
print(f"Final state at {cpu.total_cycles:,} cycles:")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  Halted: {cpu.halted}")
print(f"  Serial: {repr(cpu.memory.get_serial_output())}")
print(f"\nRecent PC values: {[f'0x{pc:04X}' for pc in pc_history[-10:]]}")
