"""
Trace test 03 RAM execution to find where the bug occurs

Focus on what happens after jumping to RAM at 0xC000
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def trace_test03():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Waiting for test 03 to start and jump to RAM...")
    print()

    last_serial_len = 0
    in_ram = False
    ram_entry_cycle = 0
    instruction_count = 0

    # Track flag changes
    last_flags = None

    while cpu.total_cycles < 30_000_000:
        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            if serial_str.strip():
                print(f"[{cpu.total_cycles:>10,}] SERIAL: {repr(serial_str)}")
            last_serial_len = current_serial_len

        pc = cpu.registers._pc

        # Check if we're in RAM (0xC000-0xDFFF)
        if 0xC000 <= pc < 0xE000:
            if not in_ram:
                in_ram = True
                ram_entry_cycle = cpu.total_cycles
                print(f"\n{'='*80}")
                print(f"[{cpu.total_cycles:>10,}] ENTERED RAM at PC=0x{pc:04X}")
                print(f"{'='*80}")
                print(f"Registers: A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
                print(f"Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
                print()
                print("Tracing RAM execution...")
                print()

            # Trace instructions in RAM
            if instruction_count < 100:  # First 100 instructions in RAM
                opcode = cpu.memory.read_byte(pc)

                # Get instruction name
                if opcode == 0xCB:
                    cb_opcode = cpu.memory.read_byte(pc + 1)
                    instr_name = f"CB {cb_opcode:02X}"
                else:
                    instr_name = OPCODES.get(opcode, ["??"])[0]

                # Save state before execution
                a_before = cpu.registers._a
                bc_before = cpu.registers.bc
                de_before = cpu.registers.de
                hl_before = cpu.registers.hl
                sp_before = cpu.registers._sp
                flags_before = (cpu.registers.flags.zero, cpu.registers.flags.subtract,
                              cpu.registers.flags.half_carry, cpu.registers.flags.carry)

                # Execute
                cpu.step()
                instruction_count += 1

                # Check state after
                a_after = cpu.registers._a
                bc_after = cpu.registers.bc
                de_after = cpu.registers.de
                hl_after = cpu.registers.hl
                sp_after = cpu.registers._sp
                flags_after = (cpu.registers.flags.zero, cpu.registers.flags.subtract,
                             cpu.registers.flags.half_carry, cpu.registers.flags.carry)

                pc_after = cpu.registers._pc

                # Log interesting changes
                changes = []
                if a_before != a_after:
                    changes.append(f"A:0x{a_before:02X}->0x{a_after:02X}")
                if bc_before != bc_after:
                    changes.append(f"BC:0x{bc_before:04X}->0x{bc_after:04X}")
                if de_before != de_after:
                    changes.append(f"DE:0x{de_before:04X}->0x{de_after:04X}")
                if hl_before != hl_after:
                    changes.append(f"HL:0x{hl_before:04X}->0x{hl_after:04X}")
                if sp_before != sp_after:
                    changes.append(f"SP:0x{sp_before:04X}->0x{sp_after:04X}")
                if flags_before != flags_after:
                    changes.append(f"F:{int(flags_before[0])}{int(flags_before[1])}{int(flags_before[2])}{int(flags_before[3])}->{int(flags_after[0])}{int(flags_after[1])}{int(flags_after[2])}{int(flags_after[3])}")

                # Print if there are changes or if it's a control flow instruction
                if changes or opcode in [0xC3, 0xCD, 0xC9, 0xC0, 0xC8, 0xD0, 0xD8]:  # JP, CALL, RET variants
                    changes_str = " ".join(changes) if changes else ""
                    print(f"  [{instruction_count:>3}] 0x{pc:04X}: {instr_name:20} -> PC=0x{pc_after:04X}  {changes_str}")

                # Check for suspicious PC values (but don't stop, just warn)
                if pc_after >= 0xC300 and instruction_count == 71:  # First time only
                    print(f"\n*** INFO: PC is at 0x{pc_after:04X} (high RAM address) ***")
                    print(f"Last instruction: 0x{pc:04X}: {instr_name}")
                    print(f"Continuing execution...\n")
            else:
                # After 500 instructions, just execute without logging
                cpu.step()
        else:
            # Not in RAM yet
            cpu.step()

    print()
    print("=" * 80)
    if in_ram:
        print(f"Total instructions executed in RAM: {instruction_count}")
        print(f"Time spent in RAM: {cpu.total_cycles - ram_entry_cycle:,} cycles")
    else:
        print("Never entered RAM")
    print("=" * 80)

if __name__ == "__main__":
    trace_test03()
