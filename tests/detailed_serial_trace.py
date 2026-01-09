"""
Capture detailed serial output including non-printable bytes
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_serial():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running and capturing ALL serial output...")
    print()

    last_serial_len = 0
    test_03_started = False

    while cpu.total_cycles < 50_000_000:
        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]

            # Show both hex and ASCII
            hex_str = ' '.join(f'{b:02X}' for b in new_bytes)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else f'<{b:02X}>' for b in new_bytes)

            print(f"[{cpu.total_cycles:>10,}] Serial: {ascii_str}")
            print(f"                Hex:    {hex_str}")

            # Check if test 03 started
            full_serial = cpu.memory._serial_output
            full_ascii = ''.join(chr(b) if 32 <= b < 127 else '' for b in full_serial)

            if '03' in full_ascii and not test_03_started:
                test_03_started = True
                print(f"\n>>> TEST 03 STARTED at cycle {cpu.total_cycles:,} <<<\n")

                # Run for 10 more seconds of cycles to see if more output comes
                print("Waiting for test 03 to output result...")
                timeout_cycles = cpu.total_cycles + 10_000_000

                while cpu.total_cycles < timeout_cycles:
                    current_serial_len2 = len(cpu.memory._serial_output)
                    if current_serial_len2 > current_serial_len:
                        new_bytes2 = cpu.memory._serial_output[current_serial_len:]
                        hex_str2 = ' '.join(f'{b:02X}' for b in new_bytes2)
                        ascii_str2 = ''.join(chr(b) if 32 <= b < 127 else f'<{b:02X}>' for b in new_bytes2)
                        print(f"[{cpu.total_cycles:>10,}] Serial: {ascii_str2}")
                        print(f"                Hex:    {hex_str2}")
                        current_serial_len = current_serial_len2

                        # Check for "ok" or "failed"
                        full_ascii = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
                        if '03:ok' in full_ascii or '03:failed' in full_ascii:
                            print("\n*** TEST 03 COMPLETED! ***\n")
                            break

                    cpu.step()

                print(f"\nNo further output after 10M cycles")
                print(f"Final PC: 0x{cpu.registers._pc:04X}")
                print(f"Total serial bytes: {len(cpu.memory._serial_output)}")
                break

            last_serial_len = current_serial_len

        cpu.step()

    print()
    print("=" * 80)
    print("Final serial output (all bytes):")
    all_bytes = cpu.memory._serial_output
    print(f"Hex: {' '.join(f'{b:02X}' for b in all_bytes)}")
    print(f"ASCII: {''.join(chr(b) if 32 <= b < 127 else f'<{b:02X}>' for b in all_bytes)}")
    print("=" * 80)

if __name__ == "__main__":
    trace_serial()
