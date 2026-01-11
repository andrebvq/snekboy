"""
Debug VRAM state during actual gameplay
Check if VRAM is being cleared/corrupted during stage selection
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def monitor_vram_during_gameplay():
    """Monitor VRAM content as the game progresses"""
    print("=" * 70)
    print("VRAM MONITORING DURING GAMEPLAY")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    checkpoints = []

    # Boot
    print("\n1. Booting...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    vram_state = check_vram_state(cpu, "After boot (title screen)")
    checkpoints.append(vram_state)

    # Press START
    print("\n2. Pressing START...")
    cpu.memory.joypad.press_button('start')
    for _ in range(50_000):
        cpu.step()
    cpu.memory.joypad.release_button('start')

    for _ in range(100_000):
        cpu.step()

    vram_state = check_vram_state(cpu, "After START pressed")
    checkpoints.append(vram_state)

    # Select game mode (press START again)
    print("\n3. Selecting game mode (START again)...")
    cpu.memory.joypad.press_button('start')
    for _ in range(50_000):
        cpu.step()
    cpu.memory.joypad.release_button('start')

    for _ in range(200_000):
        cpu.step()

    vram_state = check_vram_state(cpu, "After mode selection")
    checkpoints.append(vram_state)

    # Run more to get into actual gameplay
    print("\n4. Running to gameplay...")
    for _ in range(500_000):
        cpu.step()

    vram_state = check_vram_state(cpu, "During gameplay")
    checkpoints.append(vram_state)

    # Summary
    print("\n" + "=" * 70)
    print("VRAM STATE PROGRESSION SUMMARY")
    print("=" * 70)

    for i, state in enumerate(checkpoints):
        print(f"\n{i+1}. {state['label']}:")
        print(f"   Cycles: {state['cycles']:,}")
        print(f"   VRAM non-zero: {state['vram_nonzero']}/6144 ({state['vram_pct']:.1f}%)")
        print(f"   Tile map non-0/FF: {state['tilemap_useful']}/1024")
        print(f"   Sample: {state['sample']}")


def check_vram_state(cpu, label):
    """Check current VRAM state and return stats"""
    # Count non-zero VRAM bytes
    vram_nonzero = 0
    for addr in range(0x8000, 0x9800):
        if cpu.memory.read_byte(addr) != 0:
            vram_nonzero += 1

    vram_pct = vram_nonzero * 100 / 6144

    # Count useful tile map entries (not 0 and not FF)
    tilemap_useful = 0
    for addr in range(0x9800, 0x9C00):
        val = cpu.memory.read_byte(addr)
        if val != 0 and val != 0xFF:
            tilemap_useful += 1

    # Sample VRAM
    sample = []
    for i in range(16):
        sample.append(cpu.memory.read_byte(0x8000 + i))

    sample_str = " ".join(f"{b:02X}" for b in sample)

    # Sample tile map
    tilemap_sample = []
    for i in range(16):
        tilemap_sample.append(cpu.memory.read_byte(0x9800 + i))

    tilemap_str = " ".join(f"{b:02X}" for b in tilemap_sample)

    print(f"\n{label} ({cpu.total_cycles:,} cycles):")
    print(f"  VRAM non-zero: {vram_nonzero}/6144 ({vram_pct:.1f}%)")
    print(f"  Tile map useful: {tilemap_useful}/1024")
    print(f"  VRAM[0x8000]: {sample_str}")
    print(f"  TileMap[0x9800]: {tilemap_str}")

    # Check what tile 0xFF looks like
    tile_ff_addr = 0x8000 + (0xFF * 16)
    tile_ff_data = []
    for i in range(16):
        tile_ff_data.append(cpu.memory.read_byte(tile_ff_addr + i))

    print(f"  Tile 0xFF data: {' '.join(f'{b:02X}' for b in tile_ff_data)}")

    return {
        'label': label,
        'cycles': cpu.total_cycles,
        'vram_nonzero': vram_nonzero,
        'vram_pct': vram_pct,
        'tilemap_useful': tilemap_useful,
        'sample': sample_str,
        'tilemap': tilemap_str
    }


if __name__ == '__main__':
    monitor_vram_during_gameplay()
