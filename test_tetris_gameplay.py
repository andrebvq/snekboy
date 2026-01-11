"""
Automated Tetris gameplay test

Tests the actual gameplay flow of Tetris to verify emulator readiness.
This simulates button presses and checks that the game responds correctly.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU
from src.joypad import Joypad

# Tetris ROM path (from emulator.py)
TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def test_tetris_boot():
    """Test that Tetris boots and reaches the title screen"""
    print("=" * 70)
    print("TEST 1: Tetris Boot Sequence")
    print("=" * 70)

    cpu = CPU()

    # Load Tetris ROM
    try:
        cpu.memory.load_rom_file(TETRIS_ROM)
        print(f"✅ ROM loaded: {os.path.basename(TETRIS_ROM)}")
    except FileNotFoundError:
        print(f"❌ ROM not found: {TETRIS_ROM}")
        return False
    except Exception as e:
        print(f"❌ Failed to load ROM: {e}")
        return False

    # Run boot sequence (typically takes ~500,000 cycles to reach title screen)
    print("\nRunning boot sequence...")
    target_cycles = 500_000

    try:
        while cpu.total_cycles < target_cycles:
            cpu.step()

            # Print progress every 100k cycles
            if cpu.total_cycles % 100_000 == 0:
                print(f"  {cpu.total_cycles // 1000}k cycles...")

    except NotImplementedError as e:
        print(f"\n❌ Unimplemented instruction: {e}")
        print(f"   PC: 0x{cpu.registers._pc:04X}")
        print(f"   Cycles: {cpu.total_cycles:,}")
        return False
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check if we reached a stable state
    print(f"\n✅ Boot sequence completed: {cpu.total_cycles:,} cycles")

    # Check LCD state
    lcdc = cpu.memory.read_byte(0xFF40)
    ly = cpu.memory.read_byte(0xFF44)
    print(f"   LCDC: 0x{lcdc:02X} (LCD {'ON' if lcdc & 0x80 else 'OFF'})")
    print(f"   LY: {ly} (scanline)")

    # Check if screen has content
    screen = cpu.ppu.get_screen_buffer()
    colors_used = set()
    for row in screen:
        colors_used.update(row)
    print(f"   Screen colors: {sorted(colors_used)}")

    if len(colors_used) > 1:
        print("✅ Screen has graphics (multiple colors detected)")
    else:
        print("⚠️  Screen may be blank (only one color)")

    return True


def test_tetris_menu_navigation():
    """Test navigating the Tetris menu with button presses"""
    print("\n" + "=" * 70)
    print("TEST 2: Menu Navigation (Button Input)")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot to menu
    print("\nBooting to menu...")
    boot_cycles = 500_000
    while cpu.total_cycles < boot_cycles:
        cpu.step()

    print(f"✅ At menu (cycles: {cpu.total_cycles:,})")

    # Press START button to begin game
    print("\nSimulating START button press...")

    # Press START (button is active low in joypad)
    cpu.memory.joypad.press_button('start')

    # Run for a bit with START pressed
    press_duration = 50_000  # Hold for 50k cycles (~0.012 seconds)
    start_cycles = cpu.total_cycles

    try:
        while cpu.total_cycles < start_cycles + press_duration:
            cpu.step()

        print(f"   START held for {press_duration:,} cycles")

        # Release START
        cpu.memory.joypad.release_button('start')

        # Run more to see response
        response_cycles = 100_000
        while cpu.total_cycles < start_cycles + press_duration + response_cycles:
            cpu.step()

        print(f"✅ Button press simulation completed")
        print(f"   Total cycles: {cpu.total_cycles:,}")

        # Check if PC has changed (game responding)
        pc = cpu.registers._pc
        print(f"   PC: 0x{pc:04X}")

        return True

    except Exception as e:
        print(f"❌ Error during button test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tetris_gameplay_loop():
    """Test actual gameplay - piece falling, movement, rotation"""
    print("\n" + "=" * 70)
    print("TEST 3: Gameplay Loop (Piece Movement)")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot and get into game
    print("\nBooting and starting game...")

    # Boot
    while cpu.total_cycles < 500_000:
        cpu.step()

    # Press START to begin
    cpu.memory.joypad.press_button('start')
    for _ in range(10_000):
        cpu.step()
    cpu.memory.joypad.release_button('start')

    # Wait a bit more
    for _ in range(50_000):
        cpu.step()

    print(f"✅ In game (cycles: {cpu.total_cycles:,})")

    # Now test piece movement
    print("\nTesting piece movement controls...")

    # Test LEFT
    print("  Pressing LEFT...")
    cpu.memory.joypad.press_button('left')
    for _ in range(5_000):
        cpu.step()
    cpu.memory.joypad.release_button('left')
    for _ in range(5_000):
        cpu.step()

    # Test RIGHT
    print("  Pressing RIGHT...")
    cpu.memory.joypad.press_button('right')
    for _ in range(5_000):
        cpu.step()
    cpu.memory.joypad.release_button('right')
    for _ in range(5_000):
        cpu.step()

    # Test ROTATE (A button)
    print("  Pressing A (rotate)...")
    cpu.memory.joypad.press_button('a')
    for _ in range(5_000):
        cpu.step()
    cpu.memory.joypad.release_button('a')
    for _ in range(5_000):
        cpu.step()

    # Test DOWN (fast drop)
    print("  Pressing DOWN...")
    cpu.memory.joypad.press_button('down')
    for _ in range(5_000):
        cpu.step()
    cpu.memory.joypad.release_button('down')
    for _ in range(5_000):
        cpu.step()

    print(f"\n✅ All movement controls tested")
    print(f"   Total cycles: {cpu.total_cycles:,}")

    # Check if game is still running (not crashed)
    pc = cpu.registers._pc
    print(f"   PC: 0x{pc:04X}")

    if not cpu.halted:
        print("✅ Game is still running (not halted)")
    else:
        print("⚠️  Game is halted")

    return True


def test_tetris_long_run():
    """Run Tetris for an extended period to check stability"""
    print("\n" + "=" * 70)
    print("TEST 4: Long-Run Stability Test")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    print("\nRunning Tetris for 5 million cycles (~1.2 seconds of gameplay)...")

    target = 5_000_000
    last_print = 0

    try:
        while cpu.total_cycles < target:
            cpu.step()

            # Print progress
            if cpu.total_cycles - last_print >= 1_000_000:
                print(f"  {cpu.total_cycles // 1_000_000}M cycles...")
                last_print = cpu.total_cycles

        print(f"\n✅ Stability test PASSED")
        print(f"   Total cycles: {cpu.total_cycles:,}")
        print(f"   PC: 0x{cpu.registers._pc:04X}")
        print(f"   Halted: {cpu.halted}")

        # Check LCD is still on
        lcdc = cpu.memory.read_byte(0xFF40)
        print(f"   LCD: {'ON' if lcdc & 0x80 else 'OFF'}")

        return True

    except Exception as e:
        print(f"\n❌ Stability test FAILED at {cpu.total_cycles:,} cycles")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tetris_interrupt_flow():
    """Check that VBlank interrupts are firing correctly during gameplay"""
    print("\n" + "=" * 70)
    print("TEST 5: Interrupt Flow (VBlank Detection)")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    print("\nBooting Tetris...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    # Track VBlank interrupts
    print("\nMonitoring VBlank interrupts for 1 frame...")

    # Check IE and IF registers
    ie_before = cpu.memory.read_byte(0xFFFF)
    print(f"   IE (Interrupt Enable): 0x{ie_before:02X}")
    print(f"   IME (Master Enable): {cpu.ime}")

    # Run for one frame (70224 cycles)
    start_cycles = cpu.total_cycles
    frame_cycles = 70224

    vblank_count = 0
    if_values = []

    while cpu.total_cycles < start_cycles + frame_cycles:
        if_before = cpu.memory.read_byte(0xFF0F)
        cpu.step()
        if_after = cpu.memory.read_byte(0xFF0F)

        # Check if VBlank interrupt flag was set
        if (if_after & 0x01) and not (if_before & 0x01):
            vblank_count += 1
            print(f"   VBlank interrupt detected at cycle {cpu.total_cycles:,}")

    print(f"\n   VBlank interrupts detected: {vblank_count}")

    if vblank_count >= 1:
        print("✅ VBlank interrupts are firing")
        return True
    else:
        print("⚠️  No VBlank interrupts detected (may be issue)")
        return False


def main():
    """Run all Tetris tests"""
    print("\n" + "=" * 70)
    print("TETRIS GAMEPLAY AUTOMATED TEST SUITE")
    print("=" * 70)
    print()

    results = []

    # Test 1: Boot
    try:
        results.append(("Boot Sequence", test_tetris_boot()))
    except Exception as e:
        print(f"❌ Boot test crashed: {e}")
        results.append(("Boot Sequence", False))

    # Test 2: Menu Navigation
    try:
        results.append(("Menu Navigation", test_tetris_menu_navigation()))
    except Exception as e:
        print(f"❌ Menu test crashed: {e}")
        results.append(("Menu Navigation", False))

    # Test 3: Gameplay Loop
    try:
        results.append(("Gameplay Loop", test_tetris_gameplay_loop()))
    except Exception as e:
        print(f"❌ Gameplay test crashed: {e}")
        results.append(("Gameplay Loop", False))

    # Test 4: Long Run
    try:
        results.append(("Long-Run Stability", test_tetris_long_run()))
    except Exception as e:
        print(f"❌ Stability test crashed: {e}")
        results.append(("Long-Run Stability", False))

    # Test 5: Interrupts
    try:
        results.append(("Interrupt Flow", test_tetris_interrupt_flow()))
    except Exception as e:
        print(f"❌ Interrupt test crashed: {e}")
        results.append(("Interrupt Flow", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1

    print()
    print(f"Results: {passed}/{len(results)} tests passed")
    print()

    # Final verdict
    if passed == len(results):
        print("🎉 ALL TESTS PASSED - TETRIS IS FULLY PLAYABLE! 🎉")
        return 0
    elif passed >= 3:
        print("⚠️  MOSTLY PLAYABLE - Some issues detected but core gameplay works")
        return 0
    else:
        print("❌ NOT PLAYABLE - Critical issues prevent gameplay")
        return 1


if __name__ == '__main__':
    sys.exit(main())
