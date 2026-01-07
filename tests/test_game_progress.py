"""
Test that the game progresses beyond the initial copyright screen
and continues running without getting stuck
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Testing game progression with EI and RETI fixes...")
print()

# Track unique PC values to detect if stuck in tight loop
pc_history = []
sample_interval = 100000  # Sample PC every 100k cycles
last_sample = 0

# Run for 100 million cycles (about 100 seconds of game time)
target_cycles = 100_000_000
milestone = 10_000_000

print(f"Running for {target_cycles:,} cycles...")
print(f"Sampling PC every {sample_interval:,} cycles to detect stuck loops")
print()

stuck_threshold = 10  # If we see the same PC 10 times in a row, we're stuck

while cpu.total_cycles < target_cycles:
    cpu.step()

    # Sample PC periodically
    if cpu.total_cycles - last_sample >= sample_interval:
        pc_history.append(cpu.registers._pc)
        last_sample = cpu.total_cycles

        # Check if stuck (last 10 samples are very similar)
        if len(pc_history) >= stuck_threshold:
            recent_pcs = set(pc_history[-stuck_threshold:])
            if len(recent_pcs) <= 3:
                print(f"[{cpu.total_cycles:,}] Detected stuck loop - only {len(recent_pcs)} unique PCs")
                print(f"  Recent PCs: {', '.join(f'0x{pc:04X}' for pc in sorted(recent_pcs))}")
                print(f"  IME: {cpu.ime}")
                print(f"  IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")
                print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
                print()
                print("Game appears to be stuck. Stopping test.")
                break

    # Progress updates
    if cpu.total_cycles >= milestone:
        print(f"[{cpu.total_cycles:,}] Still running... (PC: 0x{cpu.registers._pc:04X}, IME: {cpu.ime})")
        milestone += 10_000_000

print()
print("="*70)
print("FINAL STATE:")
print("="*70)
print(f"Total cycles: {cpu.total_cycles:,}")
print(f"PC: 0x{cpu.registers._pc:04X}")
print(f"IME: {cpu.ime}")
print(f"Halted: {cpu.halted}")
print()

# Analyze PC history
unique_pcs = set(pc_history)
print(f"PC samples collected: {len(pc_history)}")
print(f"Unique PC values: {len(unique_pcs)}")

if len(unique_pcs) < 5:
    print()
    print("[PROBLEM] Very few unique PCs - game is stuck in tight loop")
    print(f"Loop addresses: {', '.join(f'0x{pc:04X}' for pc in sorted(unique_pcs))}")
elif len(unique_pcs) > 50:
    print()
    print("[SUCCESS] Game is progressing - many different code paths executed")
else:
    print()
    print("[OK] Game is running - moderate code path variety")

# Check screen state
screen = cpu.ppu.get_screen_buffer()
colors = set()
for row in screen:
    colors.update(row)

print()
print(f"Screen colors: {sorted(colors)}")
if len(colors) == 1:
    print("[INFO] Screen is solid color")
else:
    print("[OK] Screen has graphics")

# Show some samples of where execution has been
if len(unique_pcs) <= 20:
    print()
    print(f"All unique PC locations visited: {', '.join(f'0x{pc:04X}' for pc in sorted(unique_pcs))}")
