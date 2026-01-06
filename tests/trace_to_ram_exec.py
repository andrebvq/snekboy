"""
Trace until the test jumps to execute code from RAM (0xC000+)
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()
cpu.memory.load_rom_file('test_roms/halt_bug.gb')

print("Tracing until code execution from RAM...")

instruction_count = 0

while instruction_count < 100000:
    pc = cpu.registers._pc

    # Check if we're executing from RAM
    if pc >= 0xC000:
        print(f"\n{'='*80}")
        print(f"Now executing from RAM! PC=0x{pc:04X}")
        print(f"{'='*80}\n")

        # Trace next 300 instructions in detail
        for i in range(300):
            pc = cpu.registers._pc
            opcode = cpu.memory.read_byte(pc)

            # Decode instruction
            if opcode == 0xCB:
                cb_opcode = cpu.memory.read_byte(pc + 1)
                instr = f"CB [0x{cb_opcode:02X}]"
            elif opcode in OPCODES:
                name = OPCODES[opcode][0]
                length = OPCODES[opcode][1]
                operands = [cpu.memory.read_byte(pc + j + 1) for j in range(length - 1)]
                op_str = " " + ",".join(f"0x{op:02X}" for op in operands) if operands else ""
                instr = f"{name}{op_str}"
            else:
                instr = f"[0x{opcode:02X}] UNKNOWN"

            a = cpu.registers._a
            bc = cpu.registers.bc
            de = cpu.registers.de
            hl = cpu.registers.hl
            sp = cpu.registers._sp

            print(f"[{i:3d}] PC=0x{pc:04X} {instr:30s} | A=0x{a:02X} BC=0x{bc:04X} DE=0x{de:04X} HL=0x{hl:04X} SP=0x{sp:04X}")

            try:
                cpu.step()
            except NotImplementedError as e:
                print(f"\n[ERROR] Unimplemented: {e} at PC=0x{pc:04X}")
                break
            except Exception as e:
                print(f"\n[ERROR] {e} at PC=0x{pc:04X}")
                import traceback
                traceback.print_exc()
                break

        break

    try:
        cpu.step()
        instruction_count += 1
    except NotImplementedError as e:
        print(f"[ERROR] Unimplemented: {e} at PC=0x{pc:04X}")
        break
    except Exception as e:
        print(f"[ERROR] {e} at PC=0x{pc:04X}")
        break

print(f"\n\nSerial output: {cpu.memory.get_serial_output()}")
