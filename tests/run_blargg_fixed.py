"""
Run Blargg tests with FIXED ROM loading

BUG FIX: Don't overwrite I/O registers when loading ROM!
ROM should only be written to 0x0000-0x7FFF (ROM banks)
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def load_rom_correctly(cpu, rom_data):
    """Load ROM without overwriting I/O registers"""
    # ROM Bank 0: 0x0000-0x3FFF
    # ROM Bank N: 0x4000-0x7FFF
    # Total ROM area: 0x0000-0x7FFF (32KB)

    rom_size = min(len(rom_data), 0x8000)  # Max 32KB for basic ROM

    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print(f"Loaded {rom_size} bytes of ROM (0x0000-0x{rom_size-1:04X})")

    # Don't write to I/O registers (0xFF00-0xFFFF)!
    # Don't write to VRAM (0x8000-0x9FFF)
    # Don't write to other areas that aren't ROM

def run_test():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # OLD BUGGY WAY (overwrites I/O registers):
    # for i, byte in enumerate(rom_data):
    #     cpu.memory.write_byte(i, byte)

    # NEW CORRECT WAY:
    load_rom_correctly(cpu, rom_data)

    # Verify LCDC wasn't overwritten
    lcdc = cpu.memory.read_byte(0xFF40)
    print(f"LCDC after ROM load: 0x{lcdc:02X} (should be 0x91)")

    if lcdc == 0x00:
        print("ERROR: LCDC was overwritten! LCD is disabled!")
        return False

    print()
    print("Running emulation...")
    print()

    max_cycles = 30_000_000
    last_serial_len = 0

    try:
        while cpu.total_cycles < max_cycles:
            cpu.step()

            # Check serial output
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_bytes = cpu.memory._serial_output[last_serial_len:]
                for b in new_bytes:
                    if b == 0x0A:
                        print()
                    elif 32 <= b < 127:
                        print(chr(b), end='', flush=True)
                last_serial_len = current_serial_len

    except KeyboardInterrupt:
        print("\\nInterrupted")

    print()
    print("=" * 80)

    # Get full output
    serial_output = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)

    if "01:ok  02:ok  03:ok" in serial_output:
        print("SUCCESS: All tests (01, 02, 03) PASSED!")
        return True
    elif "01:ok  02:ok" in serial_output:
        print("PARTIAL: Tests 01 and 02 passed, test 03 failed or incomplete")
        return False
    else:
        print("FAILED: Tests did not complete successfully")
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
