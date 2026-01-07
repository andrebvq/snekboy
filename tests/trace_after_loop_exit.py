"""
Trace execution after the nested loop exits to see what happens next
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until we're past the initial phase
while cpu.total_cycles < 148_000:
    cpu.step()

# Fast forward until C becomes 0
print("Fast forwarding until loop exits...")
iterations = 0
while True:
    pc = cpu.registers._pc
    c_before = cpu.registers._c
    opcode = cpu.memory.read_byte(pc)

    cpu.step()
    iterations += 1

    # Check if we exited the loop
    if pc >= 0x026B and pc <= 0x0270 and cpu.registers._pc > 0x0270:
        print(f"Loop exited after {iterations} iterations")
        print(f"Exited at PC: 0x{cpu.registers._pc:04X}")
        print(f"B: {cpu.registers._b}, C: {cpu.registers._c}")
        print()
        break

    if iterations > 20000:
        print("Took too long, something's wrong")
        break

# Now trace the next 100 instructions to see what happens
print("Tracing next 100 instructions:")
print("="*80)

for i in range(100):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)
    a = cpu.registers._a
    b = cpu.registers._b
    c = cpu.registers._c
    hl = cpu.registers.hl

    cpu.step()

    pc_after = cpu.registers._pc

    # Simple opcode decoding
    if opcode == 0x00:
        name = "NOP"
    elif opcode == 0x20:
        name = "JR NZ"
    elif opcode == 0x21:
        name = "LD HL,nn"
    elif opcode == 0x0E:
        name = "LD C,n"
    elif opcode == 0x06:
        name = "LD B,n"
    elif opcode == 0x3E:
        name = "LD A,n"
    elif opcode == 0x32:
        name = "LDD (HL),A"
    elif opcode == 0x05:
        name = "DEC B"
    elif opcode == 0x0D:
        name = "DEC C"
    elif opcode == 0xC3:
        name = "JP nn"
    elif opcode == 0xCD:
        name = "CALL nn"
    elif opcode == 0xC9:
        name = "RET"
    elif opcode == 0xAF:
        name = "XOR A"
    elif opcode == 0xCB:
        name = "CB prefix"
    else:
        name = f"[0x{opcode:02X}]"

    print(f"[{i:3d}] 0x{pc:04X}: {name:15s} A:{a:02X} B:{b:02X} C:{c:02X} HL:{hl:04X} -> PC:0x{pc_after:04X}")

    # Check if we're stuck in a loop
    if pc == 0x026B:
        print(f"\n>>> BACK IN THE STUCK LOOP at iteration {i}!")
        print(f"    This means the code jumps back to 0x026B after exiting")
        break

    # Check if we hit another infinite loop
    if i > 0 and pc == pc_after:
        print(f"\n>>> STUCK at PC 0x{pc:04X}! (instruction doesn't advance PC)")
        break
