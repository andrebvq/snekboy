"""
Disassemble around 0x0861 where the failure path is chosen
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

print("Disassembling around 0x0861 (where 0x6000 is pushed):")
print("=" * 70)

addr = 0x0850
while addr < 0x0890:
    opcode = cpu.memory.read_byte(addr)
    marker = " <-- PUSH 0x6000" if addr == 0x0861 else ""

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

# Now run to just before this instruction and trace
print(f"\n{'='*70}")
print("Running to just before the PUSH and tracing...")
print(f"{'='*70}")

# Run to test 03
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        break

# Run to near 0x0861
target_cycle = 12881072 - 1000  # A bit before the push
while cpu.total_cycles < target_cycle:
    cpu.step()

# Now trace
print(f"\nTracing last ~50 instructions before PUSH:")
print("=" * 70)

trace = []
while cpu.total_cycles < 12881100:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    instr_name = OPCODES[opcode][0] if opcode in OPCODES else f"0x{opcode:02X}"

    a = cpu.registers._a
    f = cpu.registers.flags._bits.value
    hl = cpu.registers.hl

    trace_line = f"[{cpu.total_cycles:>10}] PC=0x{pc:04X} {instr_name:20s} A=0x{a:02X} F=0x{f:02X} HL=0x{hl:04X}"
    trace.append(trace_line)
    if len(trace) > 50:
        trace.pop(0)

    cpu.step()

    if pc == 0x0861:
        print("\nLast 50 instructions before PUSH 0x6000:")
        for line in trace:
            print(line)
        print(f"\n>>> A is 0x{cpu.registers._a:02X} after this push")
        break

print(f"{'='*70}")
