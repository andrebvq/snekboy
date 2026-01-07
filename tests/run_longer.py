"""
Run the emulator for a MUCH longer time to see if initialization finishes
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run for 100 million cycles to see if initialization completes
target_cycles = 100_000_000
last_report = 0
vblank_wait_count = 0  # Track how many times we hit the VBlank wait loop

print(f"Running for {target_cycles:,} cycles...")
print()

while cpu.total_cycles < target_cycles:
    try:
        pc = cpu.registers._pc

        # Track if we're at the VBlank wait loop
        if pc == 0x0233:
            vblank_wait_count += 1

        cpu.step()

        # Report every 5,000,000 cycles
        if cpu.total_cycles - last_report >= 5_000_000:
            lcdc = cpu.memory.read_byte(0xFF40)
            ly = cpu.memory.read_byte(0xFF44)
            print(f"Cycles: {cpu.total_cycles:,} | PC: 0x{pc:04X} | LCDC: 0x{lcdc:02X} | LY: {ly} | VBlank waits: {vblank_wait_count}")
            last_report = cpu.total_cycles

    except NotImplementedError as e:
        print(f"\nUnimplemented instruction at PC: 0x{cpu.registers._pc:04X}")
        print(f"Error: {e}")
        break
    except Exception as e:
        print(f"\nError at PC: 0x{cpu.registers._pc:04X}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        break

print(f"\nFinished running for {cpu.total_cycles:,} cycles")
print(f"Final PC: 0x{cpu.registers._pc:04X}")
print(f"Final LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
print(f"Final LY: {cpu.memory.read_byte(0xFF44)}")

# Check if we're still in the clearing loops
if cpu.registers._pc >= 0x026B and cpu.registers._pc <= 0x027C:
    print(f"\nStill in memory clearing routines")
    print(f"B: {cpu.registers._b}, C: {cpu.registers._c}")
else:
    print(f"\nExited memory clearing routines!")
    print(f"Code is now at 0x{cpu.registers._pc:04X}")
