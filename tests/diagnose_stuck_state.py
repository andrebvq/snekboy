"""
Comprehensive diagnostic of what Tetris is doing at 80M+ cycles
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Running to 80 million cycles...")
target = 80_000_000

# Fast forward
while cpu.total_cycles < target:
    cpu.step()

print(f"\nReached {cpu.total_cycles:,} cycles")
print("="*70)

# 1. Check CPU state
print("\n1. CPU STATE:")
print(f"   PC: 0x{cpu.registers._pc:04X}")
print(f"   SP: 0x{cpu.registers._sp:04X}")
f_value = (cpu.registers.flags.zero << 7) | (cpu.registers.flags.subtract << 6) | (cpu.registers.flags.half_carry << 5) | (cpu.registers.flags.carry << 4)
print(f"   A: 0x{cpu.registers._a:02X}  F: 0x{f_value:02X}")
print(f"   BC: 0x{cpu.registers.bc:04X}  DE: 0x{cpu.registers.de:04X}  HL: 0x{cpu.registers.hl:04X}")
print(f"   IME: {cpu.ime}")
print(f"   Halted: {cpu.halted}")

# 2. Check interrupt state
print("\n2. INTERRUPT STATE:")
ie = cpu.memory.read_byte(0xFFFF)
if_reg = cpu.memory.read_byte(0xFF0F)
print(f"   IE (0xFFFF): 0x{ie:02X} - Enabled: ", end="")
interrupts = []
if ie & 0x01: interrupts.append("VBlank")
if ie & 0x02: interrupts.append("LCD-STAT")
if ie & 0x04: interrupts.append("Timer")
if ie & 0x08: interrupts.append("Serial")
if ie & 0x10: interrupts.append("Joypad")
print(", ".join(interrupts) if interrupts else "None")

print(f"   IF (0xFF0F): 0x{if_reg:02X} - Pending: ", end="")
pending = []
if if_reg & 0x01: pending.append("VBlank")
if if_reg & 0x02: pending.append("LCD-STAT")
if if_reg & 0x04: pending.append("Timer")
if if_reg & 0x08: pending.append("Serial")
if if_reg & 0x10: pending.append("Joypad")
print(", ".join(pending) if pending else "None")

# 3. Check LCD/PPU state
print("\n3. LCD/PPU STATE:")
lcdc = cpu.memory.read_byte(0xFF40)
stat = cpu.memory.read_byte(0xFF41)
ly = cpu.memory.read_byte(0xFF44)
lyc = cpu.memory.read_byte(0xFF45)
scx = cpu.memory.read_byte(0xFF43)
scy = cpu.memory.read_byte(0xFF42)

print(f"   LCDC (0xFF40): 0x{lcdc:02X}")
print(f"     LCD Enable: {bool(lcdc & 0x80)}")
print(f"     Window Map: 0x{'9C00' if lcdc & 0x40 else '9800'}")
print(f"     Window Enable: {bool(lcdc & 0x20)}")
print(f"     BG/Win Tiles: 0x{'8000' if lcdc & 0x10 else '8800'}")
print(f"     BG Map: 0x{'9C00' if lcdc & 0x08 else '9800'}")
print(f"     Sprite Size: {'8x16' if lcdc & 0x04 else '8x8'}")
print(f"     Sprites Enable: {bool(lcdc & 0x02)}")
print(f"     BG/Win Enable: {bool(lcdc & 0x01)}")

print(f"   STAT (0xFF41): 0x{stat:02X}")
print(f"     Mode: {stat & 0x03} ({'HBlank' if (stat & 0x03) == 0 else 'VBlank' if (stat & 0x03) == 1 else 'OAM' if (stat & 0x03) == 2 else 'Transfer'})")
print(f"     LYC=LY: {bool(stat & 0x04)}")

print(f"   LY (0xFF44): {ly}")
print(f"   LYC (0xFF45): {lyc}")
print(f"   Scroll: X={scx}, Y={scy}")

# 4. Check screen buffer
print("\n4. SCREEN BUFFER:")
screen = cpu.ppu.get_screen_buffer()
colors = set()
for row in screen:
    colors.update(row)

color_counts = {0: 0, 1: 0, 2: 0, 3: 0}
for row in screen:
    for color in row:
        color_counts[color] += 1

print(f"   Colors in buffer: {sorted(colors)}")
for color, count in sorted(color_counts.items()):
    if count > 0:
        pct = (count / (160 * 144)) * 100
        print(f"     Color {color}: {count:5d} pixels ({pct:5.1f}%)")

if len(colors) == 1:
    print("   [!] Screen is solid single color")
else:
    print("   [OK] Screen has multiple colors (graphics present)")

# 5. Check joypad state
print("\n5. JOYPAD STATE:")
p1 = cpu.memory.read_byte(0xFF00)
print(f"   P1 (0xFF00): 0x{p1:02X}")
print(f"     Button keys selected: {not bool(p1 & 0x20)}")
print(f"     Dpad keys selected: {not bool(p1 & 0x10)}")
print(f"   Current button states: {cpu.memory.joypad.get_state_string()}")

# 6. Check what code is executing
print("\n6. CODE EXECUTION:")
print("   Next 20 instructions:")

seen_pcs = set()
for i in range(20):
    pc = cpu.registers._pc
    seen_pcs.add(pc)
    opcode = cpu.memory.read_byte(pc)

    # Simple decode
    names = {
        0x00: "NOP", 0x76: "HALT", 0x18: "JR n", 0x20: "JR NZ",
        0x28: "JR Z", 0x30: "JR NC", 0x38: "JR C",
        0xC3: "JP nn", 0xCD: "CALL nn", 0xC9: "RET",
        0xF0: "LDH A,(n)", 0xE0: "LDH (n),A", 0xFE: "CP n",
        0x3E: "LD A,n", 0xAF: "XOR A", 0x21: "LD HL,nn"
    }
    name = names.get(opcode, f"[0x{opcode:02X}]")

    cpu.step()
    new_pc = cpu.registers._pc

    print(f"   [{i:2d}] 0x{pc:04X}: {name:15s} -> 0x{new_pc:04X}")

if len(seen_pcs) <= 3:
    print(f"\n   [!] STUCK IN TIGHT LOOP - only {len(seen_pcs)} unique PC values")
    print(f"       Loop addresses: {', '.join(f'0x{pc:04X}' for pc in sorted(seen_pcs))}")
else:
    print(f"\n   [OK] Code is progressing through {len(seen_pcs)} different addresses")

# 7. Check timer state
print("\n7. TIMER STATE:")
div = cpu.memory.read_byte(0xFF04)
tima = cpu.memory.read_byte(0xFF05)
tma = cpu.memory.read_byte(0xFF06)
tac = cpu.memory.read_byte(0xFF07)
print(f"   DIV (0xFF04): 0x{div:02X}")
print(f"   TIMA (0xFF05): 0x{tima:02X}")
print(f"   TMA (0xFF06): 0x{tma:02X}")
print(f"   TAC (0xFF07): 0x{tac:02X}")
print(f"     Timer Enable: {bool(tac & 0x04)}")
if tac & 0x04:
    freq_map = {0: "4096 Hz", 1: "262144 Hz", 2: "65536 Hz", 3: "16384 Hz"}
    print(f"     Frequency: {freq_map[tac & 0x03]}")

# 8. Summary
print("\n" + "="*70)
print("DIAGNOSIS SUMMARY:")
print("="*70)

issues = []
if cpu.halted:
    issues.append("CPU is HALTED - waiting for interrupt")
if not cpu.ime and (if_reg & ie):
    issues.append("Interrupts pending but IME disabled")
if len(seen_pcs) <= 3:
    issues.append("CPU stuck in tight loop")
if len(colors) == 1:
    issues.append("Screen buffer has no graphics")
if not (lcdc & 0x80):
    issues.append("LCD is disabled")
if ly == 0 and cpu.ppu.cycle_counter == 0:
    issues.append("PPU not advancing")

if issues:
    print("\nPOTENTIAL ISSUES:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\nNo obvious issues detected - game may be running normally")
    print("If buttons don't work, game might be waiting for a specific screen/state")
