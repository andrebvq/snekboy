"""
Trace when and why IME gets disabled
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Tracing IME (Interrupt Master Enable) state changes...")
print()

last_ime = cpu.ime
ime_changes = 0

for i in range(2_000_000 // 4):
    pc_before = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc_before)

    cpu.step()

    new_ime = cpu.ime

    if new_ime != last_ime:
        ime_changes += 1

        # Decode the instruction that changed IME
        if opcode == 0xF3:
            instr = "DI"
        elif opcode == 0xFB:
            instr = "EI"
        else:
            instr = f"[0x{opcode:02X}]"

        print(f"[{cpu.total_cycles:,}] PC=0x{pc_before:04X}: {instr:5s} - IME: {last_ime} -> {new_ime}")

        last_ime = new_ime

        # If we've seen enough changes, check where we end up
        if ime_changes >= 20:
            print(f"\n... (stopping after 20 changes)")
            break

print(f"\nTotal IME changes in first 2M cycles: {ime_changes}")
print(f"Final IME state: {cpu.ime}")
print(f"Final PC: 0x{cpu.registers._pc:04X}")

# Check if we ever enable interrupts
if not cpu.ime:
    print("\n[PROBLEM] IME is still disabled!")
    print("The game needs interrupts enabled to progress")
else:
    print("\n[OK] IME is enabled")
