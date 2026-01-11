"""
Test that VBlank interrupts fire even when LCD is disabled
"""
from src.cpu import CPU

def test_lcd_off_vblank():
    """Test VBlank interrupt fires when LCD is off"""
    cpu = CPU()

    # Simulate boot
    cpu.simulate_boot()

    # Enable VBlank interrupt (bit 0 of IE register)
    cpu.memory.write_byte(0xFFFF, 0x01)  # IE - enable VBlank
    cpu.memory.write_byte(0xFF0F, 0x00)  # IF - clear all interrupt flags

    # Enable interrupts globally
    cpu.ime = True

    # Turn LCD OFF
    print("Turning LCD off...")
    cpu.memory.write_byte(0xFF40, 0x00)  # LCDC - LCD off

    # Clear LY to 0
    cpu.memory._data[0xFF44] = 0

    print(f"Initial state:")
    print(f"  LY: {cpu.memory.read_byte(0xFF44)}")
    print(f"  LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
    print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
    print(f"  IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")

    # Run for enough cycles to reach scanline 144 (VBlank)
    # Each scanline = 456 cycles
    # We need to reach line 144, so: 144 * 456 = 65,664 cycles
    target_cycles = 144 * 456

    print(f"\nRunning {target_cycles} cycles to reach LY=144...")
    cpu.ppu.step(target_cycles)

    ly = cpu.memory.read_byte(0xFF44)
    interrupt_flag = cpu.memory.read_byte(0xFF0F)

    print(f"\nAfter {target_cycles} cycles:")
    print(f"  LY: {ly}")
    print(f"  IF: 0x{interrupt_flag:02X}")
    print(f"  VBlank interrupt requested: {bool(interrupt_flag & 0x01)}")

    # Check that LY advanced to 144
    if ly == 144:
        print("[PASS] LY correctly advanced to 144 (VBlank region)")
    else:
        print(f"[FAIL] LY is {ly}, expected 144")
        return False

    # Check that VBlank interrupt was requested
    if interrupt_flag & 0x01:
        print("[PASS] VBlank interrupt correctly fired even with LCD off!")
        return True
    else:
        print("[FAIL] VBlank interrupt did NOT fire (this is the bug we're fixing)")
        return False

if __name__ == "__main__":
    success = test_lcd_off_vblank()
    if success:
        print("\n=== TEST PASSED ===")
        print("VBlank interrupts now work correctly when LCD is disabled!")
    else:
        print("\n=== TEST FAILED ===")
        exit(1)
