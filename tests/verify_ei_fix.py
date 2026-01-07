"""
Verify that the EI fix properly implements the 1-instruction delay
and that interrupts fire correctly after that delay
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Verifying EI instruction delay fix...")
print()

# Run to the EI instruction at 0x02BA
while cpu.registers._pc != 0x02BA:
    cpu.step()
    if cpu.total_cycles > 100_000_000:
        print("Never reached EI instruction")
        exit(1)

print(f"Reached EI instruction at cycle {cpu.total_cycles:,}")
print(f"PC: 0x{cpu.registers._pc:04X}")
print()

# Record state before EI
ime_before = cpu.ime
ei_pending_before = cpu._ei_pending
if_reg = cpu.memory.read_byte(0xFF0F)
ie_reg = cpu.memory.read_byte(0xFFFF)

print(f"Before EI instruction:")
print(f"  IME: {ime_before}")
print(f"  _ei_pending: {ei_pending_before}")
print(f"  IF: 0x{if_reg:02X}")
print(f"  IE: 0x{ie_reg:02X}")
print()

# Execute EI instruction
cpu.step()
pc_after_ei = cpu.registers._pc
ime_after_ei = cpu.ime
ei_pending_after_ei = cpu._ei_pending

print(f"After EI instruction (PC now at 0x{pc_after_ei:04X}):")
print(f"  IME: {ime_after_ei}")
print(f"  _ei_pending: {ei_pending_after_ei}")
print()

if ei_pending_after_ei != 1:
    print(f"[PROBLEM] _ei_pending should be 1 after EI, but is {ei_pending_after_ei}")
    print("Expected: EI sets counter to 2, then step() decrements to 1")
else:
    print("[OK] _ei_pending is 1 (will enable IME after next instruction)")

if ime_after_ei:
    print("[PROBLEM] IME is already True - should still be False during delay")
else:
    print("[OK] IME is still False (delay not yet complete)")

print()

# Execute the delay instruction (should be 0xAF: XOR A)
opcode = cpu.memory.read_byte(pc_after_ei)
print(f"Executing delay instruction at 0x{pc_after_ei:04X}: 0x{opcode:02X}")
cpu.step()

pc_after_delay = cpu.registers._pc
ime_after_delay = cpu.ime
ei_pending_after_delay = cpu._ei_pending
if_after_delay = cpu.memory.read_byte(0xFF0F)

print(f"After delay instruction (PC now at 0x{pc_after_delay:04X}):")
print(f"  IME: {ime_after_delay}")
print(f"  _ei_pending: {ei_pending_after_delay}")
print(f"  IF: 0x{if_after_delay:02X}")
print()

if ei_pending_after_delay != 0:
    print(f"[PROBLEM] _ei_pending should be 0 after delay, but is {ei_pending_after_delay}")
else:
    print("[OK] _ei_pending reached 0")

if not ime_after_delay:
    print("[PROBLEM] IME should be True after delay instruction completes")
else:
    print("[OK] IME is now True (interrupts enabled)")

print()

# Execute next instruction to see if interrupt fires
print("Executing next instruction to check if VBlank interrupt fires...")
opcode_next = cpu.memory.read_byte(pc_after_delay)
print(f"Next instruction at 0x{pc_after_delay:04X}: 0x{opcode_next:02X}")

cpu.step()

pc_after_next = cpu.registers._pc
ime_after_next = cpu.ime

print(f"After next instruction:")
print(f"  PC: 0x{pc_after_next:04X}")
print(f"  IME: {ime_after_next}")
print()

# Check if interrupt was serviced (PC should jump to vector, IME disabled)
if pc_after_next == 0x0040:
    print("[OK] VBlank interrupt fired! PC jumped to vector 0x0040")
    if not ime_after_next:
        print("[OK] IME disabled during interrupt service")
    else:
        print("[PROBLEM] IME should be disabled during interrupt service")
elif pc_after_next == 0x02EC:
    print("[INFO] No interrupt fired, execution continued normally to 0x02EC")
    print("This could be normal if no interrupt is pending at this exact moment")
else:
    print(f"[INFO] PC went to 0x{pc_after_next:04X}")

print()

# Now run forward to the stuck loop and see if it exits
print("Running forward to polling loop at 0x02ED...")
while cpu.registers._pc != 0x02ED:
    cpu.step()
    if cpu.total_cycles > 100_000_000:
        print("Never reached polling loop")
        exit(1)

print(f"Reached polling loop at cycle {cpu.total_cycles:,}")

# Monitor 0xFF85 to see if VBlank ISR updates it
print()
print("Monitoring 0xFF85 while in polling loop...")
ff85_value = cpu.memory.read_byte(0xFF85)
print(f"Initial value at 0xFF85: 0x{ff85_value:02X}")

# Let it run for a while
for i in range(1_000_000 // 4):
    pc_before = cpu.registers._pc
    cpu.step()

    new_value = cpu.memory.read_byte(0xFF85)
    if new_value != ff85_value:
        print(f"  [{cpu.total_cycles:,}] Value at 0xFF85 changed: 0x{ff85_value:02X} -> 0x{new_value:02X}")
        ff85_value = new_value

        if new_value != 0:
            print()
            print("[SUCCESS] 0xFF85 became non-zero!")

            # Check if loop exits
            pc_after = cpu.registers._pc
            for _ in range(10):
                cpu.step()

            final_pc = cpu.registers._pc
            if final_pc not in [0x02ED, 0x02EF, 0x02F0]:
                print(f"[SUCCESS] Loop exited! PC: 0x{pc_after:04X} -> 0x{final_pc:04X}")
                print()
                print("="*70)
                print("EI FIX VERIFICATION: PASSED")
                print("="*70)
            else:
                print(f"[PROBLEM] Still stuck in loop at 0x{final_pc:04X}")
            break

if ff85_value == 0:
    print()
    print("[PROBLEM] 0xFF85 stayed at 0x00 - VBlank ISR not updating it")
    print("This suggests interrupts may still not be firing correctly")

    # Check interrupt state
    ie = cpu.memory.read_byte(0xFFFF)
    if_reg = cpu.memory.read_byte(0xFF0F)
    print()
    print(f"Final state:")
    print(f"  IE: 0x{ie:02X}")
    print(f"  IF: 0x{if_reg:02X}")
    print(f"  IME: {cpu.ime}")
    print(f"  PC: 0x{cpu.registers._pc:04X}")
