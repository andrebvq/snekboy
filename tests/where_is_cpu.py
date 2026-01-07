"""
Check where the CPU is stuck and what it's doing
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run for a long time
print("Running for 10 million cycles...")
for _ in range(10_000_000 // 4):
    cpu.step()

print(f"\nAfter 10 million cycles:")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  SP: 0x{cpu.registers._sp:04X}")
print(f"  IME: {cpu.ime}")
print(f"  Halted: {cpu.halted}")
print(f"  IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")
print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
print(f"  LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
print(f"  LY: {cpu.memory.read_byte(0xFF44)}")

# Check what instruction is at current PC
pc = cpu.registers._pc
opcodes_at_pc = []
for i in range(10):
    opcodes_at_pc.append(cpu.memory.read_byte(pc + i))

print(f"\n  Bytes at PC: {' '.join(f'{b:02X}' for b in opcodes_at_pc)}")

# Execute next 20 instructions and see if PC changes
print(f"\nExecuting next 20 instructions:")
last_pcs = []
for i in range(20):
    old_pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(old_pc)
    cpu.step()
    new_pc = cpu.registers._pc

    if opcode == 0x00:
        name = "NOP"
    elif opcode == 0x76:
        name = "HALT"
    elif opcode == 0x18:
        name = "JR n"
    elif opcode == 0x20:
        name = "JR NZ"
    elif opcode == 0xC3:
        name = "JP nn"
    elif opcode == 0xCD:
        name = "CALL nn"
    elif opcode == 0xFE:
        name = "CP n"
    elif opcode == 0xF0:
        name = "LDH A,(n)"
    elif opcode == 0xCB:
        name = "CB prefix"
    else:
        name = f"[0x{opcode:02X}]"

    last_pcs.append((old_pc, opcode, name, new_pc))
    print(f"  [{i}] 0x{old_pc:04X}: {name:12s} (0x{opcode:02X}) -> 0x{new_pc:04X}")

# Check if we're in an infinite loop
unique_pcs = set(pc for pc, _, _, _ in last_pcs)
if len(unique_pcs) <= 5:
    print(f"\n[PROBLEM] CPU appears stuck in tight loop! Only {len(unique_pcs)} unique PCs")
    print(f"  Loop addresses: {', '.join(f'0x{pc:04X}' for pc in sorted(unique_pcs))}")
else:
    print(f"\n[OK] CPU is making progress through different addresses")
