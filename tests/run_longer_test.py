"""
Run test for longer to see complete error output
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def run_test():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running for 50,000,000 cycles...")
    last_serial_len = 0
    while cpu.total_cycles < 50_000_000:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            full_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            print(full_serial)
            last_serial_len = current_serial_len

        cpu.step()

    print(f"\nFinal serial output:")
    full_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
    print(full_serial)

if __name__ == "__main__":
    run_test()
