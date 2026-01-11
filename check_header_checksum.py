"""
Check Tetris ROM header and calculate checksum
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def check_header():
    """Check ROM header"""
    print("="*70)
    print("TETRIS ROM HEADER CHECK")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    print("\nCartridge Header:")

    # Title (0x0134-0x0143)
    title_bytes = [cpu.memory.read_byte(0x0134 + i) for i in range(16)]
    title = ''.join(chr(b) if 32 <= b < 127 else '.' for b in title_bytes)
    print(f"  Title: {title}")

    # Cartridge type (0x0147)
    cart_type = cpu.memory.read_byte(0x0147)
    cart_types = {
        0x00: "ROM ONLY",
        0x01: "MBC1",
        0x02: "MBC1+RAM",
        0x03: "MBC1+RAM+BATTERY"
    }
    print(f"  Type: 0x{cart_type:02X} ({cart_types.get(cart_type, 'Unknown')})")

    # ROM size (0x0148)
    rom_size = cpu.memory.read_byte(0x0148)
    rom_sizes = {0: "32KB", 1: "64KB", 2: "128KB", 3: "256KB", 4: "512KB"}
    print(f"  ROM Size: 0x{rom_size:02X} ({rom_sizes.get(rom_size, 'Unknown')})")

    # RAM size (0x0149)
    ram_size = cpu.memory.read_byte(0x0149)
    ram_sizes = {0: "None", 1: "2KB", 2: "8KB", 3: "32KB"}
    print(f"  RAM Size: 0x{ram_size:02X} ({ram_sizes.get(ram_size, 'Unknown')})")

    # Header checksum (0x014D)
    header_checksum = cpu.memory.read_byte(0x014D)
    print(f"  Header Checksum: 0x{header_checksum:02X}")

    # Calculate what checksum should be
    # Checksum = 0 - (sum of bytes 0x0134-0x014C) - 1
    checksum_sum = 0
    for addr in range(0x0134, 0x014D):
        checksum_sum += cpu.memory.read_byte(addr)

    calculated_checksum = (0 - checksum_sum - 1) & 0xFF
    print(f"  Calculated: 0x{calculated_checksum:02X}")

    if header_checksum == calculated_checksum:
        print(f"  Checksum: VALID")
    else:
        print(f"  Checksum: INVALID")

    # Check if checksum is 0x00 (affects F register)
    if header_checksum == 0x00:
        print(f"\n  F register should be: 0xB0 (Z=1, N=0, H=0, C=0)")
    else:
        print(f"\n  F register should be: 0xB0 (Z=1, N=0, H=1, C=1)")

    # Global checksum (0x014E-0x014F)
    global_checksum = (cpu.memory.read_byte(0x014E) << 8) | cpu.memory.read_byte(0x014F)
    print(f"\n  Global Checksum: 0x{global_checksum:04X}")

    # Nintendo logo check (0x0104-0x0133)
    print(f"\nNintendo Logo Check:")
    nintendo_logo = [
        0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B,
        0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D,
        0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E,
        0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99,
        0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC,
        0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E
    ]

    logo_match = True
    for i, expected in enumerate(nintendo_logo):
        actual = cpu.memory.read_byte(0x0104 + i)
        if actual != expected:
            logo_match = False
            print(f"  Byte {i}: Expected 0x{expected:02X}, got 0x{actual:02X}")

    if logo_match:
        print(f"  Nintendo logo: VALID")
    else:
        print(f"  Nintendo logo: INVALID")
        print(f"  Boot ROM would lock up!")


if __name__ == '__main__':
    check_header()
