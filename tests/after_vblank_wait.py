"""
See what happens after the VBlank wait loop exits
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until we exit the VBlank wait loop (PC should be 0x0239)
while cpu.registers._pc != 0x0239:
    cpu.step()
    if cpu.total_cycles > 50_000_000:
        print("Never reached 0x0239")
        exit(1)

print(f"Exited VBlank wait loop at cycle {cpu.total_cycles:,}")
print(f"PC: 0x{cpu.registers._pc:04X}")
print(f"LY: {cpu.memory.read_byte(0xFF44)}")
print()

# Execute next 100 instructions and watch for loops
print("Executing next 100 instructions:")
seen_pcs = {}

for i in range(100):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Track how many times we've been at this PC
    seen_pcs[pc] = seen_pcs.get(pc, 0) + 1

    cpu.step()

    # Simple decode
    if opcode == 0x3E:
        name = "LD A,n"
    elif opcode == 0xE0:
        name = "LDH (n),A"
    elif opcode == 0xAF:
        name = "XOR A"
    elif opcode == 0x21:
        name = "LD HL,nn"
    elif opcode == 0x0E:
        name = "LD C,n"
    elif opcode == 0xCD:
        name = "CALL nn"
    elif opcode == 0xC3:
        name = "JP nn"
    elif opcode == 0x18:
        name = "JR n"
    elif opcode == 0x20:
        name = "JR NZ"
    elif opcode == 0xF0:
        name = "LDH A,(n)"
    elif opcode == 0xFE:
        name = "CP n"
    else:
        name = f"[0x{opcode:02X}]"

    if i < 30 or seen_pcs[pc] > 5:  # Print first 30, or if we're looping
        pc_after = cpu.registers._pc
        print(f"  [{i:3d}] 0x{pc:04X}: {name:15s} -> 0x{pc_after:04X} (visited {seen_pcs[pc]}x)")

    # Check if stuck in a tight loop
    if seen_pcs[pc] > 50:
        print(f"\n[PROBLEM] Stuck in loop at 0x{pc:04X} (visited {seen_pcs[pc]} times)")
        print(f"  Opcode: 0x{opcode:02X} ({name})")
        break

# Check which PCs were visited most
print(f"\nMost visited addresses:")
for pc, count in sorted(seen_pcs.items(), key=lambda x: -x[1])[:10]:
    print(f"  0x{pc:04X}: {count} times")
