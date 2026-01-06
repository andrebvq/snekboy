"""
Analyze what's happening at the infinite loop location
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()
cpu.memory.load_rom_file('test_roms/halt_bug.gb')

# Run until we hit the loop
while cpu.total_cycles < 500_000:
    pc = cpu.registers._pc

    if pc == 0xC41F:
        print(f"At PC=0xC41F after {cpu.total_cycles:,} cycles")
        print(f"="*80)

        # Show what's around this address
        print("\nDisassembly around 0xC41F:")
        for addr in range(0xC410, 0xC430):
            op = cpu.memory.read_byte(addr)
            marker = " <<<" if addr == 0xC41F else ""
            if op in OPCODES:
                name = OPCODES[op][0]
                length = OPCODES[op][1]
                operands = [cpu.memory.read_byte(addr + j + 1) for j in range(length - 1)]
                op_str = " " + ",".join(f"0x{op:02X}" for op in operands) if operands else ""
                print(f"  0x{addr:04X}: {name}{op_str}{marker}")
            else:
                print(f"  0x{addr:04X}: [0x{op:02X}]{marker}")

        # Trace the loop for 20 iterations
        print(f"\n{'='*80}")
        print("Tracing loop iterations:")
        print(f"{'='*80}")

        for i in range(20):
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

            a = cpu.registers._a
            hl = cpu.registers.hl

            # Check what memory location is being read
            mem_val = cpu.memory.read_byte(hl) if hl < 0x10000 else 0

            print(f"[{i:2d}] PC=0x{pc:04X} {instr:30s} | A=0x{a:02X} HL=0x{hl:04X} (HL)=0x{mem_val:02X}")

            cpu.step()

        break

    cpu.step()

print(f"\nSerial output: {cpu.memory.get_serial_output()}")
