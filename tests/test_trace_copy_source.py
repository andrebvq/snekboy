"""
Trace how HL (source pointer) is set before the copy operation
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 03
print("Running to test 03...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        print(f"Test 03 started at cycle {cpu.total_cycles:,}\n")
        break

# Now trace HL changes until we reach the copy routine
print("Tracing HL changes until copy routine...")
print("=" * 70)

last_hl = cpu.registers.hl
trace_hl_changes = []

while cpu.total_cycles < 13_000_000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)
    hl_before = cpu.registers.hl

    cpu.step()

    hl_after = cpu.registers.hl

    # Track HL changes
    if hl_after != hl_before:
        instr_name = OPCODES[opcode][0] if opcode in OPCODES else f"0x{opcode:02X}"

        change_info = {
            'cycle': cpu.total_cycles,
            'pc': pc,
            'opcode': opcode,
            'instr': instr_name,
            'hl_before': hl_before,
            'hl_after': hl_after
        }
        trace_hl_changes.append(change_info)

        # Only print changes in relevant areas
        if 0x0200 <= pc <= 0x0220 or hl_after == 0x6301 or hl_after == 0x6300:
            print(f"[{cpu.total_cycles:>10}] PC=0x{pc:04X} {instr_name:15s} HL: 0x{hl_before:04X} -> 0x{hl_after:04X}")

            if hl_after == 0x6301:
                print("  ^^^ HL set to 0x6301 (FAILURE PATH SOURCE)!")

    # Stop when we reach the copy instruction
    if pc == 0x0207 and opcode == 0x12:  # LD (DE),A at the copy location
        print(f"\n{'='*70}")
        print(f"Reached copy instruction at cycle {cpu.total_cycles}")
        print(f"HL = 0x{cpu.registers.hl:04X} (this is the source for the copy)")
        break

# Print recent HL changes
print(f"\n{'='*70}")
print(f"Last 20 HL changes before copy:")
print(f"{'='*70}")
for change in trace_hl_changes[-20:]:
    marker = " <<<" if change['hl_after'] == 0x6301 else ""
    print(f"[{change['cycle']:>10}] PC=0x{change['pc']:04X} {change['instr']:15s} HL: 0x{change['hl_before']:04X} -> 0x{change['hl_after']:04X}{marker}")

# Check what's at the source addresses
print(f"\n{'='*70}")
print("Checking ROM data at potential source locations:")
print(f"{'='*70}")

# Check failure path source
print(f"\nFailure path source (0x6300):")
failure_bytes = [cpu.memory.read_byte(0x6300 + i) for i in range(16)]
print(f"  {' '.join(f'{b:02X}' for b in failure_bytes)}")

# Try to find success path - look for the "18 14" pattern
print(f"\nSearching for success path (starts with 18 14)...")
for addr in range(0x4000, 0x8000, 1):
    if cpu.memory.read_byte(addr) == 0x18 and cpu.memory.read_byte(addr + 1) == 0x14:
        # Check if next bytes match the error message pattern
        if cpu.memory.read_byte(addr + 2) == 0x04:  # Length byte
            print(f"  Found at 0x{addr:04X}")
            success_bytes = [cpu.memory.read_byte(addr + i) for i in range(16)]
            print(f"    {' '.join(f'{b:02X}' for b in success_bytes)}")
            break
