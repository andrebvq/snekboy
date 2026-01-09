"""
Check the LY register (0xFF44) value when test 03 is stuck
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def check_ly():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until test 03 is stuck in VBlank wait loop...")

    # Run until PC is at 0x0743 (the LDH A,(0x44) instruction)
    target_count = 0
    while cpu.total_cycles < 30_000_000:
        if cpu.registers._pc == 0x0743:
            target_count += 1
            if target_count >= 100:  # After 100 iterations, we're definitely stuck
                break
        cpu.step()

    if target_count < 100:
        print("Did not get stuck in VBlank wait loop")
        return

    print(f"Stuck in VBlank wait loop at cycle {cpu.total_cycles:,}")
    print()

    # Check LY register value
    ly = cpu.memory.read_byte(0xFF44)
    print(f"LY register (0xFF44) value: {ly} (0x{ly:02X})")
    print(f"Expected value: 144 (0x90) for VBlank")
    print()

    # Check LCD control register
    lcdc = cpu.memory.read_byte(0xFF40)
    print(f"LCDC register (0xFF40) value: 0x{lcdc:02X}")
    print(f"  Bit 7 (LCD Enable): {(lcdc >> 7) & 1}")
    print()

    # Check other PPU registers
    stat = cpu.memory.read_byte(0xFF41)
    scy = cpu.memory.read_byte(0xFF42)
    scx = cpu.memory.read_byte(0xFF43)
    print(f"STAT register (0xFF41): 0x{stat:02X}")
    print(f"SCY register (0xFF42): 0x{scy:02X}")
    print(f"SCX register (0xFF43): 0x{scx:02X}")
    print()

    # Check BC register
    bc = cpu.registers.bc
    print(f"BC register: 0x{bc:04X} ({bc})")
    print(f"  B: 0x{cpu.registers._b:02X} ({cpu.registers._b})")
    print(f"  C: 0x{cpu.registers._c:02X} ({cpu.registers._c})")
    print()

    # Run for 1000 more cycles and check if LY ever changes
    print("Sampling LY for next 1000 cycles...")
    ly_values = set()
    for i in range(1000):
        ly = cpu.memory.read_byte(0xFF44)
        ly_values.add(ly)
        cpu.step()

    print(f"LY values observed: {sorted(ly_values)}")
    if len(ly_values) == 1:
        print("*** LY NEVER CHANGES - This is the bug! ***")
    else:
        print(f"LY changes between {min(ly_values)} and {max(ly_values)}")

if __name__ == "__main__":
    check_ly()
