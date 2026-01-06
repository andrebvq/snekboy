"""
Trace what happens immediately after the LD HL,SP+0 instruction
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to the LD HL,SP+0 instruction
print("Running to LD HL,SP+0 at 0x065F...")
while cpu.total_cycles < 13_000_000:
    pc = cpu.registers._pc
    if pc == 0x065F and cpu.total_cycles > 12_800_000:  # After test 03 starts
        print(f"Found it at cycle {cpu.total_cycles:,}\n")
        break
    cpu.step()

# Now trace the next 100 instructions in detail
print("Tracing next 200 instructions after LD HL,SP+0:")
print("=" * 80)

for i in range(200):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    sp = cpu.registers._sp
    hl = cpu.registers.hl
    a = cpu.registers._a
    bc = (cpu.registers._b << 8) | cpu.registers._c
    de = (cpu.registers._d << 8) | cpu.registers._e
    z = int(cpu.registers.flags.zero)
    n = int(cpu.registers.flags.subtract)
    h = int(cpu.registers.flags.half_carry)
    c = int(cpu.registers.flags.carry)

    if opcode in OPCODES:
        name = OPCODES[opcode][0]
        length = OPCODES[opcode][1]
        operands = [cpu.memory.read_byte(pc + j + 1) for j in range(length - 1)]
        op_str = " " + ",".join(f"0x{op:02X}" for op in operands) if operands else ""
        instr = f"{name}{op_str}"
    elif opcode == 0xCB:
        instr = "CB (extended)"
    else:
        instr = f"[0x{opcode:02X}]"

    # Print the instruction and state
    print(f"[{i:3d}] PC=0x{pc:04X} {instr:30s} | A=0x{a:02X} BC=0x{bc:04X} DE=0x{de:04X} HL=0x{hl:04X} SP=0x{sp:04X} | Z{z}N{n}H{h}C{c}")

    # Execute
    cpu.step()

    # Check if DE changed to success or stayed failure
    de_after = (cpu.registers._d << 8) | cpu.registers._e
    if de_after != de and (de_after == 0x5300 or de_after == 0x6000):
        print(f"\n>>> DE CHANGED to 0x{de_after:04X}! <<<\n")

    # Check for test pattern - flag checks after LD HL,SP+n
    if i > 0 and i < 50:
        # Look for common test patterns
        if name in ["CP", "SUB", "AND", "OR", "XOR", "BIT"]:
            print(f"  ^^ Comparison/test instruction")
        if name in ["JP Z", "JP NZ", "JP C", "JP NC", "JR Z", "JR NZ", "JR C", "JR NC", "CALL Z", "CALL NZ", "CALL C", "CALL NC"]:
            print(f"  ^^ Conditional jump based on flags")

print(f"\n{'='*80}")
print("Final state:")
print(f"  DE = 0x{(cpu.registers._d << 8) | cpu.registers._e:04X}")
print(f"{'='*80}")
