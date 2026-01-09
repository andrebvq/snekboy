"""Find when tests actually start running"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def find_test_start():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print("Running to find when tests start...")
    print()

    last_serial_len = 0
    max_cycles = 30_000_000

    try:
        while cpu.total_cycles < max_cycles:
            cpu.step()

            # Check serial output
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_bytes = cpu.memory._serial_output[last_serial_len:]
                new_str = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02X}]' for b in new_bytes)

                print(f"[{cpu.total_cycles:>12,}] Serial: {repr(new_str)}")

                # Check for test completion markers
                full_output = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)

                if "01:ok" in full_output:
                    print(f"\n>>> TEST 01 COMPLETED at cycle {cpu.total_cycles:,}\n")

                if "02:ok" in full_output:
                    print(f"\n>>> TEST 02 COMPLETED at cycle {cpu.total_cycles:,}\n")

                if "03" in full_output and "ok" not in full_output.split("03")[1][:10]:
                    print(f"\n>>> TEST 03 MARKER at cycle {cpu.total_cycles:,}\n")

                last_serial_len = current_serial_len

    except KeyboardInterrupt:
        print("Interrupted")

    print()
    print("=" * 80)
    print(f"Final cycles: {cpu.total_cycles:,}")
    print("=" * 80)

if __name__ == "__main__":
    find_test_start()
