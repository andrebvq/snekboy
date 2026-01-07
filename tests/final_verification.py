"""
Final verification that the game progresses past the polling loop
with both EI and RETI fixes applied
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Running game to polling loop...")
print()

# Run to polling loop
while cpu.registers._pc != 0x02ED:
    cpu.step()
    if cpu.total_cycles > 100_000_000:
        print("Never reached polling loop")
        exit(1)

print(f"Reached polling loop at cycle {cpu.total_cycles:,}")
print(f"IME: {cpu.ime}")
print(f"IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")
print(f"IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")

ff85 = cpu.memory.read_byte(0xFF85)
print(f"Value at 0xFF85: 0x{ff85:02X}")
print()

if not cpu.ime:
    print("[PROBLEM] IME is False - interrupts won't fire")
    exit(1)

print("Monitoring polling loop for up to 10 seconds of emulated time...")
print("Waiting for 0xFF85 to become non-zero so loop can exit...")
print()

max_cycles = 10_000_000  # ~10 seconds at 1MHz
start_cycle = cpu.total_cycles

changes = 0
last_value = ff85

while True:
    pc_before = cpu.registers._pc
    cpu.step()

    # Check if still in loop or exited
    if cpu.total_cycles - start_cycle > max_cycles:
        print(f"Timeout after {max_cycles:,} cycles")
        break

    # Check 0xFF85 value
    new_value = cpu.memory.read_byte(0xFF85)
    if new_value != last_value:
        changes += 1
        print(f"  [{cpu.total_cycles:,}] 0xFF85 changed: 0x{last_value:02X} -> 0x{new_value:02X}")
        last_value = new_value

        if new_value != 0:
            print()
            print("[SUCCESS] 0xFF85 became non-zero!")

            # Run a few more cycles to see if loop exits
            for _ in range(100):
                cpu.step()

            final_pc = cpu.registers._pc
            print(f"PC after 100 more cycles: 0x{final_pc:04X}")

            if final_pc not in [0x02ED, 0x02EF, 0x02F0]:
                print()
                print("="*70)
                print("SUCCESS - GAME PROGRESSED PAST POLLING LOOP!")
                print("="*70)
                print()
                print(f"Final PC: 0x{final_pc:04X}")
                print(f"Total cycles: {cpu.total_cycles:,}")
                print(f"0xFF85 final value: 0x{cpu.memory.read_byte(0xFF85):02X}")
            else:
                print("[PROBLEM] Still stuck in loop despite 0xFF85 being non-zero")

            break

    # Check if we exited the loop (PC is no longer in 0x02ED-0x02F0 range)
    pc_after = cpu.registers._pc
    if pc_after not in [0x02ED, 0x02EF, 0x02F0] and pc_before in [0x02ED, 0x02EF, 0x02F0]:
        print()
        print(f"[SUCCESS] Loop exited at cycle {cpu.total_cycles:,}!")
        print(f"PC: 0x{pc_before:04X} -> 0x{pc_after:04X}")
        print(f"0xFF85 value: 0x{cpu.memory.read_byte(0xFF85):02X}")
        print()
        print("="*70)
        print("SUCCESS - GAME PROGRESSED PAST POLLING LOOP!")
        print("="*70)
        break

if changes == 0:
    print()
    print("[PROBLEM] 0xFF85 never changed - VBlank ISR not running")
elif last_value == 0:
    print()
    print("[PROBLEM] 0xFF85 stayed at 0x00 - loop won't exit")
