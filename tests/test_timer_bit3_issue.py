"""
Debug the bit 3 frequency issue
"""

from src.cpu import CPU

cpu = CPU()

print("Initial system counter:", cpu._system_counter)
print("Initial bit 3:", (cpu._system_counter >> 3) & 1)

# Configure timer for frequency 1 (bit 3)
cpu.memory.write_byte(0xFF06, 0x00)
cpu.memory.write_byte(0xFF05, 0x00)
cpu.memory.write_byte(0xFF07, 0x05)

print("\nTracing bit 3 and TIMA for 20 M-cycles:")
print("M-cycle | Counter | Bit3 | TIMA")
print("-" * 40)

for i in range(20):
    counter_before = cpu._system_counter
    bit3_before = (counter_before >> 3) & 1
    tima_before = cpu.memory.read_byte(0xFF05)

    cpu.step()

    counter_after = cpu._system_counter
    bit3_after = (counter_after >> 3) & 1
    tima_after = cpu.memory.read_byte(0xFF05)

    edge = ""
    if bit3_before == 1 and bit3_after == 0:
        edge = " <- FALLING EDGE"
    elif bit3_before == 0 and bit3_after == 1:
        edge = " <- RISING EDGE"

    tima_change = ""
    if tima_after != tima_before:
        tima_change = f" (TIMA changed: {tima_before}->{tima_after})"

    print(f"{i:7d} | {counter_before:7d} | {bit3_before:4d} | {tima_before:4d}{edge}{tima_change}")

print(f"{'Final':>7s} | {cpu._system_counter:7d} | {(cpu._system_counter >> 3) & 1:4d} | {cpu.memory.read_byte(0xFF05):4d}")
