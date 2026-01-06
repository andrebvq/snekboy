"""
Trace the delay loop at 0x0213 to see what's happening with A
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run until we enter the delay loop
while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    if pc == 0x0213:
        # We've entered the delay loop
        print("Entered delay loop at 0x0213")
        print(f"A = 0x{cpu.registers._a:02X}")
        print(f"Carry = {cpu.registers.flags.carry}")
        break
    cpu.step()

# Now trace the loop
print("\nTracing first 50 iterations:")
for i in range(50):
    pc = cpu.registers._pc
    a_before = cpu.registers._a
    c_before = cpu.registers.flags.carry

    cpu.step()

    a_after = cpu.registers._a
    c_after = cpu.registers.flags.carry

    if pc == 0x0213:  # SUB
        print(f"[{i:3d}] SUB: A: 0x{a_before:02X} -> 0x{a_after:02X}, C: {c_before} -> {c_after}")

    if pc == 0x0215 and c_after:  # JR NC when carry is set (should NOT jump)
        print(f"\n{'='*80}")
        print("Loop should exit now (carry is set, JR NC should not jump)")
        print(f"A = 0x{a_after:02X}, C = {c_after}")
        print(f"{'='*80}")
        break

    if pc != 0x0213 and pc != 0x0215:
        print(f"\nExited loop to PC=0x{pc:04X}")
        break
