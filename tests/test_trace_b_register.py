"""
Trace register B from test 02 completion to PC=0x0642
Find out why B=0x02 when it should be 0x03
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
print("Running until test 02 completes...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if "02:ok" in serial and " 03" not in serial:
        print(f"Test 02 completed at cycle {cpu.total_cycles:,}")
        print(f"B at this point: 0x{cpu.registers._b:02X}")
        break

# Now trace B register changes until we hit PC=0x0642
print("\n" + "=" * 80)
print("Tracing B register from test 02 completion to PC=0x0642:")
print("=" * 80)

last_b = cpu.registers._b
instruction_count = 0

while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    if opcode in OPCODES:
        name = OPCODES[opcode][0]
        length = OPCODES[opcode][1]
        operands = [cpu.memory.read_byte(pc + j + 1) for j in range(length - 1)]
        op_str = " " + ",".join(f"0x{op:02X}" for op in operands) if operands else ""
        instr = f"{name}{op_str}"
    else:
        instr = f"[0x{opcode:02X}]"

    b_before = cpu.registers._b

    # Execute
    cpu.step()
    instruction_count += 1

    b_after = cpu.registers._b

    # Print if B changed
    if b_after != b_before:
        print(f"[{instruction_count:5d}] PC=0x{pc:04X} {instr:30s} B: 0x{b_before:02X} -> 0x{b_after:02X}")
        last_b = b_after

    # Check serial output
    serial = cpu.memory.get_serial_output()
    if " 03" in serial and instruction_count > 100:
        print(f"\n{'='*80}")
        print(f"Test 03 started at instruction {instruction_count}")
        print(f"B = 0x{cpu.registers._b:02X}")
        print(f"{'='*80}\n")

    # Stop when we hit the LD A,B at 0x0642 (where B is read)
    if pc == 0x0642:
        print(f"\n{'='*80}")
        print(f"Reached LD A,B at 0x0642 (where test number is used)")
        print(f"B = 0x{cpu.registers._b:02X}")
        print(f"This should be 0x03 for test 03, but it's 0x{cpu.registers._b:02X}")
        print(f"{'='*80}")
        break

print(f"\nTotal instructions traced: {instruction_count}")
