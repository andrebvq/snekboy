"""
Trace execution from ISR return (0x019C) to polling loop (0x02ED)
to see if/where IME should be re-enabled
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Running to ISR return point...")
print()

# Run to right before the VBlank ISR returns
# We'll run to the first VBlank interrupt
while cpu.registers._pc != 0x02BA:
    cpu.step()

cpu.step()  # EI
cpu.step()  # Delay

# This triggers interrupt, now fast-forward to ISR return
while True:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    cpu.step()

    # Break when we return from the ISR (back to 0x019C)
    if pc == 0x21E4 and opcode == 0xC0:  # RET NZ instruction
        break

print(f"ISR returned to PC: 0x{cpu.registers._pc:04X}")
print(f"IME: {cpu.ime}")
print()

# Now trace execution from here to polling loop
print("Tracing from ISR return to polling loop:")
print()

seen_pcs = []
ei_or_reti_seen = False

while cpu.registers._pc != 0x02ED:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Track important instructions
    names = {
        0xF3: "DI", 0xFB: "EI", 0xD9: "RETI",
        0x00: "NOP", 0x76: "HALT",
        0xC3: "JP", 0xCD: "CALL", 0xC9: "RET",
        0x18: "JR", 0x20: "JR NZ", 0x28: "JR Z",
        0xF0: "LDH A,(n)", 0xE0: "LDH (n),A",
        0xAF: "XOR A", 0xA7: "AND A",
    }
    instr_name = names.get(opcode, f"[0x{opcode:02X}]")

    ime_before = cpu.ime

    cpu.step()

    pc_after = cpu.registers._pc
    ime_after = cpu.ime

    # Only print significant instructions or IME changes
    if opcode in [0xF3, 0xFB, 0xD9] or ime_before != ime_after or len(seen_pcs) < 20:
        print(f"  0x{pc:04X}: {instr_name:15s} (IME: {ime_before}) -> 0x{pc_after:04X} (IME: {ime_after})")

        if opcode == 0xFB:
            ei_or_reti_seen = True
            print("    ^ EI instruction - interrupts should be enabled after delay")
        elif opcode == 0xD9:
            ei_or_reti_seen = True
            print("    ^ RETI instruction - interrupts should be enabled immediately")
        elif opcode == 0xF3:
            print("    ^ DI instruction - interrupts disabled")

    seen_pcs.append(pc)

    if cpu.total_cycles > 100_000_000:
        print()
        print("Timeout - never reached polling loop")
        exit(1)

print()
print(f"Reached polling loop at 0x02ED (cycle {cpu.total_cycles:,})")
print(f"IME: {cpu.ime}")
print(f"Total instructions traced: {len(seen_pcs)}")
print()

if not ei_or_reti_seen:
    print("[PROBLEM] No EI or RETI instruction found between ISR return and polling loop")
    print("This explains why IME is False - it was never re-enabled!")
    print()
    print("The VBlank ISR used RET instead of RETI, so IME stayed False")
    print("The game code should have another EI to re-enable interrupts, but doesn't")

ie = cpu.memory.read_byte(0xFFFF)
if_reg = cpu.memory.read_byte(0xFF0F)
ff85 = cpu.memory.read_byte(0xFF85)

print(f"State at polling loop:")
print(f"  IE: 0x{ie:02X}")
print(f"  IF: 0x{if_reg:02X}")
print(f"  IME: {cpu.ime}")
print(f"  0xFF85: 0x{ff85:02X}")
