"""
Analyze the context around the delay loop at 0x0213 to understand
what condition the test is waiting for
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def analyze_delay_context():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Disassemble around 0x0213 to understand the flow
    print("=" * 80)
    print("Disassembly around delay loop (0x0200-0x0220)")
    print("=" * 80)

    pc = 0x0200
    while pc < 0x0220:
        opcode = cpu.memory.read_byte(pc)
        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
            length = 2
        else:
            instr_info = OPCODES.get(opcode, ["??", 1])
            instr_name = instr_info[0]
            length = instr_info[1]

        # Get operand bytes
        operands = []
        for i in range(1, length):
            operands.append(cpu.memory.read_byte(pc + i))

        # Format
        bytes_str = f"{opcode:02X}"
        for op in operands:
            bytes_str += f" {op:02X}"
        bytes_str = bytes_str.ljust(12)

        operands_str = " ".join(f"0x{op:02X}" for op in operands) if operands else ""

        marker = " <-- Delay loop" if pc == 0x0213 else ""
        print(f"  0x{pc:04X}: {bytes_str} {instr_name:20} {operands_str}{marker}")

        pc += length

    print()
    print("=" * 80)
    print("Running test and tracing when we hit 0x0213...")
    print("=" * 80)

    # Run until we hit 0x0213 multiple times
    hit_count = 0
    last_hit_cycle = 0

    while cpu.total_cycles < 30_000_000 and hit_count < 10:
        pc = cpu.registers._pc

        if pc == 0x0213:
            hit_count += 1
            cycles_since_last = cpu.total_cycles - last_hit_cycle if last_hit_cycle > 0 else 0

            print(f"\nHit #{hit_count} at cycle {cpu.total_cycles:,} (+{cycles_since_last} since last)")
            print(f"  A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
            print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")

            # Show what called us (return address on stack)
            ret_low = cpu.memory.read_byte(cpu.registers._sp)
            ret_high = cpu.memory.read_byte(cpu.registers._sp + 1)
            ret_addr = ret_low | (ret_high << 8)
            print(f"  Return address on stack: 0x{ret_addr:04X}")

            # Check some key registers
            ly = cpu.memory.read_byte(0xFF44)
            print(f"  LY=0x{ly:02X} ({ly})")

            last_hit_cycle = cpu.total_cycles

            # Trace next 20 instructions to see the pattern
            if hit_count == 1:
                print("\n  Tracing next 20 instructions:")
                for i in range(20):
                    pc_trace = cpu.registers._pc
                    opcode = cpu.memory.read_byte(pc_trace)
                    instr_name = OPCODES.get(opcode, ["??"])[0]
                    cpu.step()
                    pc_after = cpu.registers._pc
                    print(f"    [{i+1:>2}] 0x{pc_trace:04X}: {instr_name:20} -> PC=0x{pc_after:04X}")
                continue

        cpu.step()

if __name__ == "__main__":
    analyze_delay_context()
