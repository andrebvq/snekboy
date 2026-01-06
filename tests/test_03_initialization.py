"""
Trace what happens immediately after "03" is printed to understand test 03 initialization
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run until "02:ok" is complete
print("Running until test 02 completes...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if "02:ok" in serial and " 03" not in serial:
        print(f"Test 02 completed at cycle {cpu.total_cycles:,}")
        print(f"Serial: {repr(serial)}")
        print(f"DE at this point: 0x{(cpu.registers._d << 8) | cpu.registers._e:04X}")
        break

# Now trace until "03" is printed
print("\n" + "=" * 80)
print("Tracing from test 02 completion to test 03 start:")
print("=" * 80)

last_serial = serial
instruction_count = 0

while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Get instruction name
    if opcode in OPCODES:
        name = OPCODES[opcode][0]
    else:
        name = f"0x{opcode:02X}"

    de_before = (cpu.registers._d << 8) | cpu.registers._e
    a_before = cpu.registers._a

    # Execute
    cpu.step()
    instruction_count += 1

    de_after = (cpu.registers._d << 8) | cpu.registers._e

    # Check for DE changes
    if de_after != de_before:
        print(f"\n[{instruction_count:5d}] PC=0x{pc:04X} {name:20s} DE: 0x{de_before:04X} -> 0x{de_after:04X}")

    # Check for serial output
    serial = cpu.memory.get_serial_output()
    if serial != last_serial:
        new_chars = serial[len(last_serial):]
        print(f"\n{'='*80}")
        print(f"[{instruction_count:5d}] SERIAL OUTPUT: {repr(new_chars)}")
        print(f"  Current DE: 0x{de_after:04X}")
        print(f"  Current A: 0x{cpu.registers._a:02X}")
        print(f"{'='*80}")
        last_serial = serial

        if " 03" in new_chars:
            print("\nTest 03 just started!")
            print(f"Total instructions between test 02 completion and test 03 start: {instruction_count}")
            print(f"\nFinal state when test 03 starts:")
            print(f"  PC: 0x{cpu.registers._pc:04X}")
            print(f"  DE: 0x{(cpu.registers._d << 8) | cpu.registers._e:04X}")
            print(f"  A: 0x{cpu.registers._a:02X}")
            print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
            break

print(f"\n{'='*80}")

# Now let's see what the FIRST actual test instruction in test 03 is
print("\nTracing the next 50 instructions to see what test 03 does:")
print("=" * 80)

for i in range(50):
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

    de = (cpu.registers._d << 8) | cpu.registers._e
    a = cpu.registers._a

    print(f"[{i:3d}] PC=0x{pc:04X} {instr:30s} | DE=0x{de:04X} A=0x{a:02X}")

    cpu.step()

    # Check if DE changes
    de_new = (cpu.registers._d << 8) | cpu.registers._e
    if de_new != de:
        print(f"      >>> DE changed to 0x{de_new:04X}")

print(f"{'='*80}")
