"""
Check if LY ever reaches 144
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def check_ly_reaches_144():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running and monitoring LY register...")

    last_ly = -1
    ly_sequence = []
    max_ly_seen = 0

    for i in range(500_000):
        ly = cpu.memory.read_byte(0xFF44)

        if ly != last_ly:
            ly_sequence.append(ly)
            if ly > max_ly_seen:
                max_ly_seen = ly

            if ly == 144:
                print(f"LY reached 144 at cycle {cpu.total_cycles:,}!")
                print(f"PC: 0x{cpu.registers._pc:04X}")
                break

            # Detect wraparound
            if last_ly > ly and last_ly > 100:
                print(f"LY wrapped from {last_ly} to {ly} at cycle {cpu.total_cycles:,}")
                if max_ly_seen < 144:
                    print(f"*** BUG: LY never reached 144! Max value was {max_ly_seen} ***")
                max_ly_seen = ly  # Reset for next cycle

            last_ly = ly

        cpu.step()

    print()
    print(f"Max LY value seen: {max_ly_seen}")
    print(f"Last {min(20, len(ly_sequence))} LY values: {ly_sequence[-20:]}")

if __name__ == "__main__":
    check_ly_reaches_144()
