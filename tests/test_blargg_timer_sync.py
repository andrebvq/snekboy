"""
Test timer synchronization like Blargg does
"""

from src.cpu import CPU

cpu = CPU()

# Initialize timer like Blargg does
print("Initializing timer...")
cpu.memory.write_byte(0xFF06, 0x00)  # TMA = 0
cpu.memory.write_byte(0xFF07, 0x05)  # TAC = 0x05 (262144 Hz)

# Test the start_timer synchronization
# The idea is: write 0 to TIMA, then loop reading until it's non-zero
# This synchronizes to the exact cycle when TIMA increments

print("\nSimulating start_timer synchronization:")
print("Writing 0 to TIMA and waiting for it to increment...")

cpu.memory.write_byte(0xFF05, 0x00)  # TIMA = 0

# Loop: read TIMA, check if zero, repeat
# In assembly this is:
#   - loop: lda TIMA (3 cycles)
#           or a (1 cycle)
#           jr nz, loop (3 cycles if taken)
# Total: 7 cycles per iteration if TIMA is still 0

max_iterations = 10
for i in range(max_iterations):
    # Read TIMA (simulate LDA TIMA - 3 M-cycles)
    for _ in range(3):
        cpu.step()

    tima = cpu.memory.read_byte(0xFF05)

    # OR A (1 M-cycle)
    cpu.step()

    print(f"  Iteration {i}: TIMA={tima}")

    if tima != 0:
        print(f"  -> TIMA became non-zero after ~{cpu.total_cycles} T-cycles")
        break

    # JR NZ (3 M-cycles when taken, but we're simulating the taken branch)
    for _ in range(3):
        cpu.step()

    print(f"     Total cycles so far: {cpu.total_cycles}")

print(f"\nFinal TIMA: {cpu.memory.read_byte(0xFF05)}")
print(f"Final system counter: {cpu._system_counter}")

# The key question: does TIMA increment at predictable 16 T-cycle intervals?
print("\n" + "="*80)
print("Testing if TIMA increments every exactly 16 T-cycles...")

cpu2 = CPU()
cpu2.memory.write_byte(0xFF06, 0x00)
cpu2.memory.write_byte(0xFF07, 0x05)
cpu2.memory.write_byte(0xFF05, 0x00)

# Wait for first increment
while cpu2.memory.read_byte(0xFF05) == 0 and cpu2.total_cycles < 1000:
    cpu2.step()

first_increment_cycle = cpu2.total_cycles
print(f"First increment at T-cycle: {first_increment_cycle}")

# Now check the next few increments
increments = [first_increment_cycle]
for i in range(5):
    prev_tima = cpu2.memory.read_byte(0xFF05)
    while cpu2.memory.read_byte(0xFF05) == prev_tima and cpu2.total_cycles < first_increment_cycle + 1000:
        cpu2.step()
    increments.append(cpu2.total_cycles)
    print(f"Increment {i+2} at T-cycle: {cpu2.total_cycles} (delta: {cpu2.total_cycles - increments[-2]})")

# Check if intervals are exactly 16
intervals = [increments[i+1] - increments[i] for i in range(len(increments)-1)]
if all(interval == 16 for interval in intervals):
    print("\n[PASS] TIMA increments exactly every 16 T-cycles")
else:
    print(f"\n[FAIL] TIMA increment intervals: {intervals}")
    print(f"       Expected all 16, got varying intervals")
