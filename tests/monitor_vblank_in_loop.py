"""
Monitor VBlank interrupts while in the polling loop
to see if they're firing and what they're doing
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Running to polling loop...")

# Run to polling loop
while cpu.registers._pc != 0x02ED:
    cpu.step()

print(f"At polling loop (cycle {cpu.total_cycles:,})")
print(f"IME: {cpu.ime}")
print(f"IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")
print(f"IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
print(f"0xFF85: 0x{cpu.memory.read_byte(0xFF85):02X}")
print()

# Monitor for interrupts
print("Monitoring for VBlank interrupts while in loop...")
print("(Will track PC jumps to 0x0040 which indicates interrupt fired)")
print()

interrupt_count = 0
max_cycles = 5_000_000
start_cycle = cpu.total_cycles
last_ff85 = cpu.memory.read_byte(0xFF85)

while cpu.total_cycles - start_cycle < max_cycles:
    pc_before = cpu.registers._pc
    ime_before = cpu.ime
    if_before = cpu.memory.read_byte(0xFF0F)

    cpu.step()

    pc_after = cpu.registers._pc

    # Check for interrupt (PC jumps to vector)
    if pc_after == 0x0040 and pc_before != 0x003F:
        interrupt_count += 1
        print(f"[{cpu.total_cycles:,}] VBlank interrupt #{interrupt_count} fired")
        print(f"  PC: 0x{pc_before:04X} -> 0x{pc_after:04X}")
        print(f"  IME before: {ime_before}, IF before: 0x{if_before:02X}")

        # Trace through the ISR to see what it does
        isr_steps = 0
        max_isr_steps = 200

        while isr_steps < max_isr_steps:
            isr_pc = cpu.registers._pc
            opcode = cpu.memory.read_byte(isr_pc)

            # Check for return from ISR
            if opcode == 0xD9:  # RETI
                cpu.step()
                return_pc = cpu.registers._pc
                print(f"  ISR completed with RETI after {isr_steps + 1} steps, returned to 0x{return_pc:04X}")
                break
            elif opcode in [0xC9, 0xC0, 0xC8, 0xD0, 0xD8]:  # Various RET instructions
                cpu.step()
                return_pc = cpu.registers._pc
                print(f"  ISR completed with RET after {isr_steps + 1} steps, returned to 0x{return_pc:04X}")
                break

            cpu.step()
            isr_steps += 1

        if isr_steps >= max_isr_steps:
            print(f"  [WARNING] ISR didn't return after {max_isr_steps} steps")

        # Check 0xFF85 after ISR
        new_ff85 = cpu.memory.read_byte(0xFF85)
        if new_ff85 != last_ff85:
            print(f"  0xFF85 changed: 0x{last_ff85:02X} -> 0x{new_ff85:02X}")
            last_ff85 = new_ff85
        else:
            print(f"  0xFF85 unchanged: 0x{new_ff85:02X}")

        print()

        # Stop if we've seen enough
        if interrupt_count >= 5:
            print(f"Stopping after {interrupt_count} interrupts")
            break

    # Check if loop exited
    if pc_before in [0x02ED, 0x02EF, 0x02F0] and pc_after not in [0x02ED, 0x02EF, 0x02F0]:
        print(f"[{cpu.total_cycles:,}] Loop exited!")
        print(f"  PC: 0x{pc_before:04X} -> 0x{pc_after:04X}")
        print(f"  0xFF85: 0x{cpu.memory.read_byte(0xFF85):02X}")
        break

print()
print(f"Total interrupts observed: {interrupt_count}")
print(f"Final 0xFF85 value: 0x{cpu.memory.read_byte(0xFF85):02X}")
print(f"Final PC: 0x{cpu.registers._pc:04X}")
print(f"Final IME: {cpu.ime}")

if interrupt_count == 0:
    print()
    print("[PROBLEM] No VBlank interrupts fired")
    print("Even though IME is True, interrupts aren't triggering")

    # Check interrupt conditions
    ie = cpu.memory.read_byte(0xFFFF)
    if_reg = cpu.memory.read_byte(0xFF0F)
    print(f"IE: 0x{ie:02X} (VBlank enabled: {bool(ie & 0x01)})")
    print(f"IF: 0x{if_reg:02X} (VBlank pending: {bool(if_reg & 0x01)})")
