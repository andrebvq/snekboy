"""
Trace standalone test 03 execution to find the failure
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_standalone():
    cpu = CPU()

    rom_path = "test_roms/03-op_sp_hl.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Tracing standalone 03-op sp,hl.gb test...")
    print("=" * 80)

    # Run until we see "Failed" in output
    last_serial_len = 0
    serial_log = []

    while cpu.total_cycles < 50_000_000:
        current_serial_len = len(cpu.memory._serial_output)

        if current_serial_len > last_serial_len:
            # New serial output
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            for byte in new_bytes:
                char = chr(byte) if 32 <= byte < 127 else f'<{byte:02X}>'
                serial_log.append((cpu.total_cycles, byte, char))

            last_serial_len = current_serial_len

            # Check if we hit "Failed"
            current_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if 'Failed' in current_serial:
                print(f"'Failed' detected at cycle {cpu.total_cycles:,}")
                break

        cpu.step()

    print("\nSerial output log:")
    print("-" * 80)
    for cycle, byte, char in serial_log:
        print(f"[{cycle:>10,}] 0x{byte:02X} = '{char}'")

    print()
    print("-" * 80)
    full_serial = ''.join(chr(b) if 32 <= b < 127 else '?' for b in cpu.memory._serial_output)
    print(f"Full output: {full_serial}")

    # Print as raw bytes
    print(f"\nRaw bytes: {' '.join(f'{b:02X}' for b in cpu.memory._serial_output)}")

if __name__ == "__main__":
    trace_standalone()
