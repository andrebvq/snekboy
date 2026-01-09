"""
Trace the actual CRC routine execution from Blargg test ROM

The CRC routine is at 0x645E. Let's trace its execution to find flag bugs.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def trace_crc_execution():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Tracing CRC routine calls...")
    print()

    # The CRC routine is typically called via CALL 0x645E or similar
    # Let's find when it's called during test execution

    crc_addr = 0x645E
    crc_call_count = 0
    last_serial_len = 0

    test_03_started = False

    while cpu.total_cycles < 30_000_000:  # Run longer to reach test 03
        pc_before = cpu.registers._pc

        # Check if we're about to call the CRC routine
        opcode = cpu.memory.read_byte(pc_before)
        if opcode == 0xCD:  # CALL nn
            target_low = cpu.memory.read_byte(pc_before + 1)
            target_high = cpu.memory.read_byte(pc_before + 2)
            target = target_low | (target_high << 8)

            if target == crc_addr:
                crc_call_count += 1
                print(f"[{cpu.total_cycles:>9,}] CRC CALL #{crc_call_count} from PC=0x{pc_before:04X}")
                print(f"  Registers before: A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X}")
                print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")

                # Execute the CALL
                cpu.step()

                # Now trace through the CRC routine
                print(f"  Entering CRC routine...")

                crc_steps = 0
                max_crc_steps = 200  # Safety limit

                while cpu.registers._pc >= crc_addr and cpu.registers._pc < crc_addr + 0x100 and crc_steps < max_crc_steps:
                    pc = cpu.registers._pc
                    a_before = cpu.registers._a
                    flags_before = (cpu.registers.flags.zero, cpu.registers.flags.subtract,
                                  cpu.registers.flags.half_carry, cpu.registers.flags.carry)

                    cpu.step()
                    crc_steps += 1

                    a_after = cpu.registers._a
                    flags_after = (cpu.registers.flags.zero, cpu.registers.flags.subtract,
                                 cpu.registers.flags.half_carry, cpu.registers.flags.carry)

                    # Log flag changes or A changes
                    if a_before != a_after or flags_before != flags_after:
                        opcode = cpu.memory.read_byte(pc)
                        instr_name = OPCODES.get(opcode, ["??"])[0]
                        print(f"    0x{pc:04X}: {instr_name:15} A:0x{a_before:02X}->0x{a_after:02X} Z{int(flags_before[0])}{int(flags_after[0])} N{int(flags_before[1])}{int(flags_after[1])} H{int(flags_before[2])}{int(flags_after[2])} C{int(flags_before[3])}{int(flags_after[3])}")

                print(f"  CRC returned after {crc_steps} steps")
                print(f"  Registers after: A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X}")
                print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
                print()

                if crc_call_count >= 5:  # Trace first 5 CRC calls
                    break
                continue

        cpu.step()

        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            if serial_str.strip():
                print(f"[{cpu.total_cycles:>9,}] SERIAL: {repr(serial_str)}")
                # Check if test 03 started
                if '03' in serial_str and not test_03_started:
                    test_03_started = True
                    print(f">>> TEST 03 STARTED - Now watching for CRC calls <<<")
            last_serial_len = current_serial_len

    print()
    print("=" * 80)
    print(f"Total CRC calls traced: {crc_call_count}")
    print("=" * 80)

if __name__ == "__main__":
    trace_crc_execution()
