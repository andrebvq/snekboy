"""
Trace B and C together to see if there's a LD B,C instruction
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run until test 02 completes
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if "02:ok" in serial and " 03" not in serial:
        print(f"Test 02 completed")
        print(f"B=0x{cpu.registers._b:02X}, C=0x{cpu.registers._c:02X}")
        break

# Now trace until we hit 0x0642, looking for LD B,C (opcode 0x41)
print("\nLooking for LD B,C (opcode 0x41)...")
instruction_count = 0

while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    b_before = cpu.registers._b
    c_before = cpu.registers._c

    # Check if this is LD B,C
    if opcode == 0x41:
        print(f"\n{'='*80}")
        print(f"Found LD B,C at PC=0x{pc:04X}!")
        print(f"Before: B=0x{b_before:02X}, C=0x{c_before:02X}")

    cpu.step()
    instruction_count += 1

    b_after = cpu.registers._b
    c_after = cpu.registers._c

    if opcode == 0x41:
        print(f"After:  B=0x{b_after:02X}, C=0x{c_after:02X}")
        print(f"{'='*80}\n")

    # Stop when we hit 0x0642
    if pc == 0x0642:
        print(f"\nReached PC=0x0642 (LD A,B)")
        print(f"Final B=0x{cpu.registers._b:02X}, C=0x{cpu.registers._c:02X}")
        print(f"B should be 0x03 (from C) but is 0x{cpu.registers._b:02X}")
        break

print(f"\nTotal instructions: {instruction_count}")
