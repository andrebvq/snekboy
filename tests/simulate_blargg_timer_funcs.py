"""
Simulate exactly what Blargg's start_timer and stop_timer functions do
"""

from src.cpu import CPU

def simulate_start_timer(cpu):
    """
    Simulate Blargg's start_timer:
    -    xor  a         ; 1 M-cycle
         sta  TIMA      ; 3 M-cycles
         lda  TIMA      ; 3 M-cycles
         or   a         ; 1 M-cycle
         jr   nz,-      ; 3 M-cycles (if taken)
    """
    print("\nSimulating start_timer...")

    # Loop until TIMA != 0
    iterations = 0
    while iterations < 10:
        # XOR A (1 M-cycle)
        cpu.step()

        # STA TIMA (3 M-cycles) - write 0 to TIMA
        for _ in range(3):
            cpu.step()
        cpu.memory.write_byte(0xFF05, 0x00)

        # LDA TIMA (3 M-cycles) - read TIMA
        for _ in range(3):
            cpu.step()
        tima = cpu.memory.read_byte(0xFF05)

        # OR A (1 M-cycle)
        cpu.step()

        print(f"  Iteration {iterations}: TIMA={tima}, T-cycle={cpu.total_cycles}")

        if tima != 0:
            # Would exit loop
            print(f"  -> Synchronized! TIMA became non-zero")
            break

        # JR NZ (3 M-cycles, taken)
        for _ in range(3):
            cpu.step()

        iterations += 1

    return tima

def simulate_stop_timer(cpu):
    """
    Simulate Blargg's stop_timer_word (simplified):
    - Reads TIMA, subtracts 5, multiplies by 4
    - Then does sync loop again
    - Returns cycle count in DE
    """
    print("\nSimulating stop_timer...")

    tima = cpu.memory.read_byte(0xFF05)
    print(f"  TIMA at stop: {tima}")

    # Calculate main count: (TIMA - 5) * 4
    if tima < 5:
        print(f"  [WARNING] TIMA < 5, this would cause issues")
        return 999

    main_count = (tima - 5) * 4
    print(f"  Main count: (TIMA - 5) * 4 = ({tima} - 5) * 4 = {main_count}")

    # Do sync loop to get remaining cycles
    # Similar to start_timer
    remaining = 0
    for i in range(20):
        # Write 0 to TIMA, wait for it to become non-zero
        # XOR A, STA TIMA, LDA TIMA, DEC DE, OR A, JR NZ
        # Total: 1 + 3 + 3 + 2 + 1 + 3 = 13 M-cycles per iteration

        for _ in range(8):  # Simplified: just run cycles
            cpu.step()

        cpu.memory.write_byte(0xFF05, 0x00)

        for _ in range(3):
            cpu.step()

        tima_check = cpu.memory.read_byte(0xFF05)

        for _ in range(2):
            cpu.step()

        remaining = i
        if tima_check != 0:
            break

    total = main_count + remaining
    print(f"  Remaining: {remaining}")
    print(f"  Total timing offset: {total}")

    return total

# Test it
print("="*80)
print("Testing Blargg timer functions simulation")
print("="*80)

cpu = CPU()

# Initialize timer
cpu.memory.write_byte(0xFF06, 0x00)  # TMA = 0
cpu.memory.write_byte(0xFF07, 0x05)  # TAC = enable + 262144 Hz

# Call start_timer
tima_after_start = simulate_start_timer(cpu)

# Do some work (simulate test instructions)
print(f"\nDoing work...")
for _ in range(100):  # 100 M-cycles of work
    cpu.step()

# Call stop_timer
timing_offset = simulate_stop_timer(cpu)

print(f"\n{'='*80}")
print(f"Result: timing offset = {timing_offset}")
print(f"Expected: 0 (if timer is perfect)")
if timing_offset == 0:
    print("[PASS]")
else:
    print(f"[FAIL] Got {timing_offset} instead of 0")
