"""
Run test 03 for much longer to see if it eventually completes
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def run_test03_longer():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running test 03 for extended time...")
    print("Will run up to 100M cycles (instead of usual 30M)")
    print()

    last_serial_len = 0
    last_print_cycle = 0
    print_interval = 10_000_000  # Print status every 10M cycles

    max_cycles = 100_000_000

    while cpu.total_cycles < max_cycles:
        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            if serial_str.strip():
                print(f"[{cpu.total_cycles:>10,}] SERIAL: {repr(serial_str)}")
            last_serial_len = current_serial_len

        # Print progress
        if cpu.total_cycles - last_print_cycle >= print_interval:
            print(f"[{cpu.total_cycles:>10,}] Still running... PC=0x{cpu.registers._pc:04X}")
            last_print_cycle = cpu.total_cycles

        cpu.step()

    print()
    print("=" * 80)
    print(f"Reached {max_cycles:,} cycles")
    print(f"Final PC: 0x{cpu.registers._pc:04X}")
    print(f"Total serial output characters: {len(cpu.memory._serial_output)}")
    print("=" * 80)

if __name__ == "__main__":
    run_test03_longer()
