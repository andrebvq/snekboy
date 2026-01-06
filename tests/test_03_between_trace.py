"""
Trace what happens between the LD HL,SP+n and the halt
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to just after the LD HL,SP+n instruction
print("Running to the LD HL,SP+n instruction...")
target_cycle = 12882156  # From previous trace
while cpu.total_cycles < target_cycle + 100:
    if cpu.total_cycles >= target_cycle - 10:
        pc = cpu.registers._pc
        if pc == 0x065F:
            print(f"At LD HL,SP+n at cycle {cpu.total_cycles}")
            cpu.step()  # Execute it
            break
    cpu.step()

print(f"After LD HL,SP+n: PC=0x{cpu.registers._pc:04X}, cycle={cpu.total_cycles}\n")

# Now trace execution until halt
print("Tracing execution until halt or error...")
print("=" * 70)

trace_lines = []
last_serial = cpu.memory.get_serial_output()

for i in range(200000):  # Trace up to 200k instructions
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Get instruction name
    if opcode in OPCODES:
        name = OPCODES[opcode][0]
        length = OPCODES[opcode][1]
        # Get operands
        operands = [cpu.memory.read_byte(pc + j + 1) for j in range(length - 1)]
        op_str = " " + ",".join(f"0x{op:02X}" for op in operands) if operands else ""
        instr_str = f"{name}{op_str}"
    elif opcode == 0xCB:
        instr_str = "CB (extended)"
    else:
        instr_str = f"[UNKNOWN 0x{opcode:02X}]"

    # Record trace
    sp = cpu.registers._sp
    hl = cpu.registers.hl
    a = cpu.registers._a
    f = cpu.registers.flags._bits.value
    trace_line = f"[{cpu.total_cycles:>10}] PC=0x{pc:04X} {instr_str:30s} A=0x{a:02X} F=0x{f:02X} SP=0x{sp:04X} HL=0x{hl:04X}"

    trace_lines.append(trace_line)
    if len(trace_lines) > 100:
        trace_lines.pop(0)

    # Execute
    cpu.step()

    # Check for serial changes
    serial = cpu.memory.get_serial_output()
    if serial != last_serial:
        print(f"\n[SERIAL at {cpu.total_cycles}] {repr(serial[len(last_serial):])}")
        last_serial = serial

    # Check if halted
    if cpu.halted:
        print(f"\n{'='*70}")
        print(f"CPU HALTED at cycle {cpu.total_cycles}, PC=0x{cpu.registers._pc:04X}")
        print(f"{'='*70}")
        print("\nLast 100 instructions before halt:")
        for line in trace_lines:
            print(line)
        break

    # Check if we hit the error message area
    if 0xC302 <= cpu.registers._pc <= 0xC314:
        print(f"\n{'='*70}")
        print(f"PC entered error message data area!")
        print(f"{'='*70}")
        print("\nLast 100 instructions:")
        for line in trace_lines:
            print(line)
        break

print(f"\n{'='*70}")
print(f"Final state:")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  Halted: {cpu.halted}")
print(f"  Serial: {repr(cpu.memory.get_serial_output())}")
print(f"{'='*70}")
