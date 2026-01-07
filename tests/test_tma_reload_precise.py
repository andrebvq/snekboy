"""
Test precise TMA reload timing
"""

from src.cpu import CPU

cpu = CPU()

print("Testing TMA reload precise timing...")
print("="*80)

# Setup
cpu.memory.write_byte(0xFF06, 0xAB)  # TMA
cpu.memory.write_byte(0xFF05, 0xFE)  # TIMA close to overflow
cpu.memory.write_byte(0xFF07, 0x05)  # Enable timer

print(f"Initial: TIMA=0x{cpu.memory.read_byte(0xFF05):02X}, TMA=0x{cpu.memory.read_byte(0xFF06):02X}")

# Run until overflow
for i in range(20):
    cpu.step()
    tima = cpu.memory.read_byte(0xFF05)
    if_reg = cpu.memory.read_byte(0xFF0F)
    overflow_status = cpu._timer_overflow_cycles

    print(f"  Step {i+1}: T-cycle {cpu.total_cycles:3d}, TIMA=0x{tima:02X}, IF=0x{if_reg:02X}, overflow_cycles={overflow_status}")

    # According to Game Boy behavior:
    # - Cycle N: TIMA increments from 0xFF to 0x00 (but still reads as 0x00)
    # - Cycle N+1: TIMA reads as 0x00, interrupt flag is set, TIMA is loaded with TMA
    # So TIMA should never increment past TMA value

    if (if_reg & 0x04) != 0 and tima != 0xAB:
        print(f"\n[ISSUE] Interrupt flag set but TIMA=0x{tima:02X} instead of TMA=0xAB")
        break

print("\n" + "="*80)
print("Expected behavior:")
print("  - TIMA increments from 0xFE -> 0xFF -> 0x00")
print("  - One M-cycle later: IF bit 2 set, TIMA = TMA (0xAB)")
print("  - TIMA should NEVER be 0xAC or higher")
