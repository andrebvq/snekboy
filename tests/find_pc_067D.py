"""
Search for PC=0x067D (the INC B that should increment test counter)

This should happen after each test completes.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def search():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Searching for PC=0x067D...")
    print()

    last_serial_len = 0
    pc_067D_count = 0

    while cpu.total_cycles < 15_000_000:
        pc_before = cpu.registers._pc

        if pc_before == 0x067D:
            b_before = cpu.registers._b
            cpu.step()
            b_after = cpu.registers._b

            pc_067D_count += 1
            print(f"[{cpu.total_cycles:>12,}] Hit PC=0x067D (occurrence #{pc_067D_count})")
            print(f"    B: 0x{b_before:02X} -> 0x{b_after:02X}")

            # Check serial output
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            print(f"    Serial so far: {repr(serial_str[-30:])}")
            print()
            continue

        cpu.step()

        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            if serial_str.strip():
                print(f"[{cpu.total_cycles:>12,}] SERIAL: {repr(serial_str)}")
            last_serial_len = current_serial_len

    print()
    print("=" * 80)
    print(f"Total PC=0x067D hits: {pc_067D_count}")
    print("=" * 80)

if __name__ == "__main__":
    search()
