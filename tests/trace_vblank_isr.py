"""
Trace execution through the VBlank ISR to see what it does
and verify RETI re-enables interrupts
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Tracing VBlank ISR execution...")
print()

# Run to the EI instruction
while cpu.registers._pc != 0x02BA:
    cpu.step()

print(f"At EI instruction (cycle {cpu.total_cycles:,})")

# Execute EI and delay instruction
cpu.step()  # EI
cpu.step()  # Delay instruction (XOR A)

print(f"After EI delay, IME: {cpu.ime}")
print()

# Next instruction should trigger VBlank interrupt
print("Executing next instruction to trigger VBlank...")
pc_before_interrupt = cpu.registers._pc
opcode = cpu.memory.read_byte(pc_before_interrupt)
print(f"Instruction at 0x{pc_before_interrupt:04X}: 0x{opcode:02X}")

cpu.step()

pc_after = cpu.registers._pc
print(f"After step: PC jumped to 0x{pc_after:04X}")

if pc_after == 0x0040:
    print("[OK] VBlank interrupt fired (jumped to vector 0x0040)")
    print()
    print("Tracing ISR execution:")
    print()

    # Trace through the ISR
    instr_count = 0
    max_instructions = 100

    while instr_count < max_instructions:
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        # Check for RETI (0xD9) or RET instructions
        if opcode == 0xD9:
            instr_name = "RETI"
            is_return = True
        elif opcode == 0xC9:
            instr_name = "RET"
            is_return = True
        elif opcode == 0xC0:
            instr_name = "RET NZ"
            is_return = not cpu.registers.flags.zero
        elif opcode == 0xC8:
            instr_name = "RET Z"
            is_return = cpu.registers.flags.zero
        elif opcode == 0xD0:
            instr_name = "RET NC"
            is_return = not cpu.registers.flags.carry
        elif opcode == 0xD8:
            instr_name = "RET C"
            is_return = cpu.registers.flags.carry
        else:
            # Simple instruction names for common ones
            names = {
                0x00: "NOP", 0x76: "HALT", 0xF3: "DI", 0xFB: "EI",
                0xC3: "JP", 0xCD: "CALL", 0x18: "JR",
                0xF0: "LDH A,(n)", 0xE0: "LDH (n),A",
                0x3E: "LD A,n", 0xAF: "XOR A", 0xA7: "AND A",
                0x06: "LD B,n", 0x0E: "LD C,n", 0x16: "LD D,n", 0x1E: "LD E,n",
                0x21: "LD HL,nn", 0x01: "LD BC,nn",
                0xEA: "LD (nn),A", 0xFA: "LD A,(nn)",
                0x32: "LD (HL-),A", 0x22: "LD (HL+),A",
                0x2A: "LD A,(HL+)", 0x3A: "LD A,(HL-)",
            }
            instr_name = names.get(opcode, f"[0x{opcode:02X}]")
            is_return = False

        ime_before = cpu.ime
        sp_before = cpu.registers._sp

        cpu.step()

        pc_after_step = cpu.registers._pc
        ime_after = cpu.ime
        sp_after = cpu.registers._sp

        print(f"  [{instr_count:2d}] 0x{pc:04X}: {instr_name:15s} (IME: {ime_before}) -> 0x{pc_after_step:04X} (IME: {ime_after})", end="")

        if sp_before != sp_after:
            print(f" [SP: 0x{sp_before:04X} -> 0x{sp_after:04X}]", end="")

        print()

        if is_return:
            if opcode == 0xD9:
                print()
                print(f"  RETI executed. IME after: {ime_after}")
                if ime_after:
                    print("  [OK] RETI re-enabled interrupts")
                else:
                    print("  [PROBLEM] RETI did not re-enable interrupts")
            else:
                print()
                print(f"  RET instruction executed. IME after: {ime_after}")

            print(f"  Returned to PC: 0x{pc_after_step:04X}")
            break

        instr_count += 1

    if instr_count >= max_instructions:
        print()
        print(f"[WARNING] ISR didn't return after {max_instructions} instructions")

    # Check what value 0xFF85 has after ISR
    ff85_after_isr = cpu.memory.read_byte(0xFF85)
    print()
    print(f"Value at 0xFF85 after ISR: 0x{ff85_after_isr:02X}")

    # Continue to polling loop
    print()
    print("Continuing to polling loop...")
    while cpu.registers._pc != 0x02ED:
        cpu.step()
        if cpu.total_cycles > 100_000_000:
            print("Never reached polling loop")
            exit(1)

    print(f"Reached polling loop at cycle {cpu.total_cycles:,}")
    print(f"IME at polling loop: {cpu.ime}")
    print(f"Value at 0xFF85: 0x{cpu.memory.read_byte(0xFF85):02X}")

    ie = cpu.memory.read_byte(0xFFFF)
    if_reg = cpu.memory.read_byte(0xFF0F)
    print(f"IE: 0x{ie:02X}, IF: 0x{if_reg:02X}")

    if not cpu.ime:
        print()
        print("[PROBLEM] IME is disabled at polling loop")
        print("This prevents VBlank interrupts from firing to update 0xFF85")
        print()
        print("Need to investigate why IME got disabled between ISR return and polling loop")

else:
    print(f"[PROBLEM] Expected PC to jump to 0x0040, but went to 0x{pc_after:04X}")
