"""
Trace register A from test 02 completion to where it becomes 0x60
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
        print(f"A at this point: 0x{cpu.registers._a:02X}")
        break

# Now trace A register changes until we hit PC=0x0652
print("\n" + "=" * 80)
print("Tracing A register from test 02 completion to PC=0x0652:")
print("=" * 80)

last_a = cpu.registers._a
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

    a_before = cpu.registers._a

    # Execute
    cpu.step()
    instruction_count += 1

    a_after = cpu.registers._a

    # Print if A changed or if we're near PC=0x0652
    if a_after != a_before or (pc >= 0x064C and pc <= 0x0655):
        print(f"[{instruction_count:5d}] PC=0x{pc:04X} {instr:30s} A: 0x{a_before:02X} -> 0x{a_after:02X}")
        last_a = a_after

    # Stop when we hit the LD D,A at 0x0652
    if pc == 0x0652:
        print(f"\n{'='*80}")
        print(f"Reached LD D,A at 0x0652")
        print(f"A = 0x{cpu.registers._a:02X}")
        print(f"About to execute: LD D,A which will set D=0x{cpu.registers._a:02X}")
        print(f"{'='*80}")
        break

print(f"\nTotal instructions traced: {instruction_count}")
