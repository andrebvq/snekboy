"""
Verify DIV bit mapping based on the Reddit discussion

According to the info:
- Internal 16-bit counter increments every M-cycle
- DIV register = upper 8 bits of this counter
- So DIV = counter[15:8], which means counter >> 8

But our implementation does: DIV = counter // 256

Let's verify these are equivalent:
- counter // 256 = counter >> 8 (integer division by 256)

And verify the bit positions for TIMA frequencies:
- The internal counter increments every M-cycle
- TIMA increments on falling edges of specific bits:
  - Freq 0 (4096 Hz):   bit 9  (increments every 512 M-cycles = 2048 T-cycles)
  - Freq 1 (262144 Hz): bit 3  (increments every 8 M-cycles = 32 T-cycles)
  - Freq 2 (65536 Hz):  bit 5  (increments every 32 M-cycles = 128 T-cycles)
  - Freq 3 (16384 Hz):  bit 7  (increments every 128 M-cycles = 512 T-cycles)

Wait, this doesn't match! Let me recalculate:
- If counter increments every M-cycle (by 1), and we want TIMA to increment every 16 T-cycles (4 M-cycles):
  - Bit 2 would toggle every 4 increments (every 4 M-cycles)
  - Falling edge on bit 2 happens every 8 M-cycles

Hmm, our counter increments by 4 every M-cycle (in T-cycle units), not by 1.
Let me think about this differently...
"""

from src.cpu import CPU

print("Testing bit mapping with our implementation")
print("="*80)

# Our implementation: counter increments by 4 every M-cycle
# So after N M-cycles, counter = N * 4

# DIV should increment every 256 T-cycles = 64 M-cycles
# At 64 M-cycles: counter = 64 * 4 = 256
# DIV = 256 // 256 = 1 ✓

# For TIMA at 262144 Hz (16 T-cycles = 4 M-cycles per increment):
# At 4 M-cycles: counter = 16
# We want a bit that toggles, so falling edge happens every 8 M-cycles
# At 8 M-cycles: counter = 32 (0x20)
# At 16 M-cycles: counter = 64 (0x40)

# Bit 3 of counter (value 8):
# counter=0-7: bit 3 = 0
# counter=8-15: bit 3 = 1
# counter=16-23: bit 3 = 0  <- falling edge at counter=16 = 4 M-cycles
# counter=24-31: bit 3 = 1
# counter=32-39: bit 3 = 0  <- falling edge at counter=32 = 8 M-cycles

# So bit 3 has falling edges at counter = 16, 48, 80, ... (every 32 T-cycles = 8 M-cycles)
# But we want falling edges every 16 T-cycles = 4 M-cycles!

print("\nLet me trace bit 3 values for first 64 T-cycles:")
for t_cycle in range(0, 65, 4):  # Every M-cycle
    bit3 = (t_cycle >> 3) & 1
    print(f"  T-cycle {t_cycle:2d}: counter={t_cycle:2d}, bit3={bit3}")

print("\nActually, the issue is clear:")
print("  - Bit 3 toggles every 8 T-cycles")
print("  - Falling edge happens every 16 T-cycles")
print("  - This matches the 262144 Hz requirement! [OK]")

print("\nLet me verify all frequencies:")

frequencies = [
    (0, 9, 1024, "4096 Hz"),
    (1, 3, 16, "262144 Hz"),
    (2, 5, 64, "65536 Hz"),
    (3, 7, 256, "16384 Hz"),
]

for freq_id, bit_pos, expected_period, name in frequencies:
    # Bit toggles every 2^bit_pos T-cycles
    # Falling edge happens every 2^(bit_pos+1) T-cycles
    toggle_period = 2 ** bit_pos
    falling_edge_period = 2 ** (bit_pos + 1)

    status = "[OK]" if falling_edge_period == expected_period else "[FAIL]"
    print(f"\n{status} Freq {freq_id} ({name}):")
    print(f"    Bit {bit_pos}: toggles every {toggle_period} T-cycles")
    print(f"    Falling edge every {falling_edge_period} T-cycles")
    print(f"    Expected period: {expected_period} T-cycles")

print("\n" + "="*80)
print("Conclusion: Our bit positions are CORRECT! [OK]")
print("The counter increments in T-cycle units (by 4 every M-cycle),")
print("and the bit positions we use produce the correct falling edge periods.")
