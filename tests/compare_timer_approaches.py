"""
Compare our falling-edge approach vs. the countdown approach from the article
"""

from src.cpu import CPU

print("Comparing timer approaches")
print("="*80)

# Our approach: falling edge detection on system counter
print("\n1. Our Approach (Falling Edge Detection):")
print("-" * 80)

cpu = CPU()
cpu.memory.write_byte(0xFF06, 0x00)  # TMA = 0
cpu.memory.write_byte(0xFF05, 0x00)  # TIMA = 0
cpu.memory.write_byte(0xFF07, 0x05)  # TAC = enable + 262144 Hz

print(f"Initial: TIMA={cpu.memory.read_byte(0xFF05)}, sys_counter={cpu._system_counter}")

# Run for exactly 64 T-cycles (16 M-cycles)
# Should see TIMA increment 4 times (every 16 T-cycles)
for i in range(16):
    cpu.step()
    if (i+1) % 4 == 0:  # Every 16 T-cycles
        tima = cpu.memory.read_byte(0xFF05)
        sys = cpu._system_counter
        print(f"  After {(i+1)*4:2d} T-cycles: TIMA={tima}, sys_counter={sys}")

# Simulate the countdown approach
print("\n2. Article's Approach (Countdown Timer):")
print("-" * 80)

# Simulate timer counter that counts down
timer_counter = 16  # For 262144 Hz
tima_countdown = 0
t_cycles = 0

print(f"Initial: TIMA={tima_countdown}, timer_counter={timer_counter}")

for i in range(16):
    # Each step is 4 T-cycles (1 M-cycle)
    t_cycles += 4
    timer_counter -= 4

    if timer_counter <= 0:
        tima_countdown += 1
        timer_counter = 16  # Reset

    if (i+1) % 4 == 0:  # Every 16 T-cycles
        print(f"  After {t_cycles:2d} T-cycles: TIMA={tima_countdown}, timer_counter={timer_counter}")

print("\n" + "="*80)
print("Analysis:")
print("  Both approaches should produce the same result for basic operation.")
print("  The falling-edge approach is more hardware-accurate.")
print("  The countdown approach is simpler but equivalent.")

# But let's check what happens with writes to TIMA
print("\n3. Testing TIMA Write During Counting:")
print("-" * 80)

cpu2 = CPU()
cpu2.memory.write_byte(0xFF06, 0x00)
cpu2.memory.write_byte(0xFF05, 0x00)
cpu2.memory.write_byte(0xFF07, 0x05)

# Run for 8 T-cycles (halfway to first increment)
for _ in range(2):
    cpu2.step()

print(f"After 8 T-cycles: TIMA={cpu2.memory.read_byte(0xFF05)}, sys_counter={cpu2._system_counter}")

# Now write to TIMA
print("Writing 100 to TIMA...")
cpu2.memory.write_byte(0xFF05, 100)

# Run for another 8 T-cycles (should complete the 16 T-cycle period)
for _ in range(2):
    cpu2.step()

tima = cpu2.memory.read_byte(0xFF05)
print(f"After another 8 T-cycles: TIMA={tima}")
print(f"Expected: TIMA=101 (should increment from 100)")

if tima == 101:
    print("  [PASS] TIMA incremented correctly after write")
else:
    print(f"  [ISSUE] TIMA={tima}, expected 101")
