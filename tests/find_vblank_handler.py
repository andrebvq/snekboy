"""
Find what should be writing to 0xFF85 - likely the VBlank ISR
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Checking interrupt vector table...")
print()

# Game Boy interrupt vectors:
# 0x0040: VBlank
# 0x0048: LCD STAT
# 0x0050: Timer
# 0x0058: Serial
# 0x0060: Joypad

vectors = {
    0x0040: "VBlank",
    0x0048: "LCD STAT",
    0x0050: "Timer",
    0x0058: "Serial",
    0x0060: "Joypad"
}

for addr, name in vectors.items():
    # Read first 3 bytes of each vector
    bytes_at_vector = [cpu.memory.read_byte(addr + i) for i in range(3)]

    print(f"{name:10s} (0x{addr:04X}): {' '.join(f'{b:02X}' for b in bytes_at_vector)}", end="")

    # Check if it's a JP instruction (0xC3)
    if bytes_at_vector[0] == 0xC3:
        # JP nn - jump to handler
        handler_addr = bytes_at_vector[1] | (bytes_at_vector[2] << 8)
        print(f"  -> JP 0x{handler_addr:04X}")
    elif bytes_at_vector[0] == 0x00:
        print(f"  -> NOP (no handler)")
    else:
        print(f"  -> Inline code")

print()

# Check VBlank handler specifically
vblank_vector = cpu.memory.read_byte(0x0040)
print(f"VBlank vector instruction: 0x{vblank_vector:02X}")

if vblank_vector == 0xC3:  # JP
    handler_addr = cpu.memory.read_byte(0x0041) | (cpu.memory.read_byte(0x0042) << 8)
    print(f"VBlank handler is at: 0x{handler_addr:04X}")
    print()

    # Read first 20 bytes of handler
    print(f"First 20 bytes of VBlank handler:")
    for i in range(20):
        byte = cpu.memory.read_byte(handler_addr + i)
        print(f"  0x{handler_addr + i:04X}: 0x{byte:02X}")

        # Look for writes to 0xFF85
        # E0 85 = LDH (0xFF85),A
        # EA 85 FF = LD (0xFF85),A
        if byte == 0xE0:
            next_byte = cpu.memory.read_byte(handler_addr + i + 1)
            if next_byte == 0x85:
                print(f"         ^^^ FOUND: LDH (0xFF85),A - writes to our target address!")
        elif byte == 0xEA:
            addr_low = cpu.memory.read_byte(handler_addr + i + 1)
            addr_high = cpu.memory.read_byte(handler_addr + i + 2)
            if addr_low == 0x85 and addr_high == 0xFF:
                print(f"         ^^^ FOUND: LD (0xFF85),A - writes to our target address!")
    print()

# Now simulate what happens if we manually trigger VBlank handler
print("Testing if VBlank handler would update 0xFF85...")
print()

# Run to the stuck loop
while cpu.registers._pc != 0x02ED:
    cpu.step()
    if cpu.total_cycles > 100_000_000:
        break

print(f"At stuck loop, 0xFF85 = 0x{cpu.memory.read_byte(0xFF85):02X}")

# Manually enable IME and see if interrupt fires
print("Enabling IME...")
cpu.ime = True

# Step a few cycles - interrupt should be serviced
print("Stepping with IME enabled...")
for i in range(100):
    old_pc = cpu.registers._pc
    old_85 = cpu.memory.read_byte(0xFF85)

    cpu.step()

    new_pc = cpu.registers._pc
    new_85 = cpu.memory.read_byte(0xFF85)

    if new_85 != old_85:
        print(f"  Step {i}: 0xFF85 changed from 0x{old_85:02X} to 0x{new_85:02X}")
        print(f"  PC: 0x{old_pc:04X} -> 0x{new_pc:04X}")

    # Check if we jumped to interrupt vector
    if old_pc == 0x02ED and new_pc == 0x0040:
        print(f"  [!] VBlank interrupt fired! Jumped to vector 0x0040")

    # Check if we exited the loop
    if old_pc in [0x02ED, 0x02EF, 0x02F0] and new_pc not in [0x02ED, 0x02EF, 0x02F0]:
        print(f"  [!] Exited stuck loop! PC now at 0x{new_pc:04X}")
        break

final_85 = cpu.memory.read_byte(0xFF85)
print(f"\nAfter 100 steps with IME enabled:")
print(f"  0xFF85 = 0x{final_85:02X}")
print(f"  PC = 0x{cpu.registers._pc:04X}")

if final_85 != 0:
    print("  [OK] VBlank handler updated 0xFF85!")
else:
    print("  [PROBLEM] 0xFF85 still zero even with interrupts enabled")
