"""
Run standalone 03-op sp,hl.gb ROM to get specific error details
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def run_standalone():
    cpu = CPU()

    rom_path = "test_roms/03-op_sp_hl.gb"
    try:
        with open(rom_path, 'rb') as f:
            rom_data = f.read()
    except FileNotFoundError:
        print(f"ERROR: {rom_path} not found!")
        return

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running standalone 03-op sp,hl.gb test...")
    print("=" * 80)

    last_serial = ""
    last_update_cycle = 0

    while cpu.total_cycles < 100_000_000:
        current_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)

        if current_serial != last_serial:
            # Print incremental output
            new_chars = current_serial[len(last_serial):]
            print(new_chars, end='', flush=True)
            last_serial = current_serial
            last_update_cycle = cpu.total_cycles

            # Check if test completed
            if ':ok' in current_serial or 'Passed' in current_serial:
                print(f"\n\nTest PASSED at cycle {cpu.total_cycles:,}")
                break
            elif 'Failed' in current_serial:
                print(f"\n\nTest FAILED at cycle {cpu.total_cycles:,}")
                print(f"Full output:\n{current_serial}")
                break

        # Timeout if no output for too long
        if cpu.total_cycles - last_update_cycle > 10_000_000:
            print(f"\n\nTimeout: No output for 10M cycles")
            print(f"Last output: {last_serial}")
            break

        cpu.step()

    print()
    print("=" * 80)
    print(f"Final output ({len(cpu.memory._serial_output)} bytes):")
    print(last_serial)
    print("=" * 80)

if __name__ == "__main__":
    run_standalone()
