"""
Trace what happens after "03" is printed

The output shows "03" but never "03:ok", meaning test 03 starts but fails.
Let's see what happens right after "03" is printed.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until '03' is printed...")

    last_serial_len = 0
    found_03 = False

    while cpu.total_cycles < 15_000_000:
        cpu.step()

        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)

            if '03' in serial_str and not found_03:
                found_03 = True
                print(f"\nFound '03' at cycle {cpu.total_cycles:,}")
                print(f"Full output so far: {repr(serial_str)}")
                print(f"\nPC after '03': 0x{cpu.registers._pc:04X}")
                print()
                print("=" * 80)
                print("TRACING NEXT 1000 INSTRUCTIONS")
                print("=" * 80)
                print()

                # Trace next 1000 instructions
                for i in range(1000):
                    pc_before = cpu.registers._pc
                    a_before = cpu.registers._a
                    b_before = cpu.registers._b

                    cpu.step()

                    # Print significant events
                    new_serial_len = len(cpu.memory._serial_output)
                    if new_serial_len > current_serial_len:
                        new_bytes_2 = cpu.memory._serial_output[current_serial_len:new_serial_len]
                        new_str = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02X}]' for b in new_bytes_2)
                        print(f"[{cpu.total_cycles:>12,}] >>> SERIAL: {repr(new_str)}")
                        current_serial_len = new_serial_len

                    # Print when entering/exiting key routines
                    if pc_before in [0x067D, 0x0652, 0x0222, 0x0213]:
                        from src.opcodes import OPCODES
                        opcode = cpu.memory.read_byte(pc_before)
                        instr = OPCODES.get(opcode, ["??"])[0]
                        print(f"[{cpu.total_cycles:>12,}] PC=0x{pc_before:04X}: {instr:20} | A=0x{a_before:02X} B=0x{b_before:02X}")

                return

            last_serial_len = current_serial_len

    print("Did not find '03' in output")

if __name__ == "__main__":
    trace()
