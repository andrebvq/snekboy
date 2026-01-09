"""Quick test to verify tests 01 and 02 still pass"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.memory import Memory

def run_rom(rom_path, max_cycles=30_000_000):
    cpu = CPU()

    # Load ROM
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print(f"Loaded {len(rom_data)} bytes of ROM at address 0x0000")

    # Run emulation
    print(f"Running: {rom_path}")
    print(f"Max cycles: {max_cycles:,}")

    try:
        while cpu.total_cycles < max_cycles:
            cpu.step()
    except KeyboardInterrupt:
        print("\\nEmulation interrupted by user")
    except Exception as e:
        print(f"\\nEmulation error: {e}")
        import traceback
        traceback.print_exc()

    # Get serial output
    serial_output = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02X}]' for b in cpu.memory._serial_output)

    print("=" * 70)
    print("SERIAL OUTPUT:")
    print("=" * 70)
    print(serial_output)
    print("=" * 70)
    print()

    # Check if test passed
    if "01:ok  02:ok" in serial_output:
        print("RESULT: Tests 01 and 02 PASSED!")
        return True
    else:
        print("RESULT: Tests failed or incomplete")
        return False

if __name__ == "__main__":
    rom_path = "test_roms/cpu_instrs.gb"
    success = run_rom(rom_path)
    sys.exit(0 if success else 1)
