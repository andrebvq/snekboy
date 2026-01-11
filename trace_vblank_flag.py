"""
Trace VBlank flag (0xFF85) writes to see who sets it and when
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

# Track flag writes
flag_writes = []
flag_reads = []

original_write = None
original_read = None

def traced_write(address, value):
    if address == 0xFF85:
        pc = traced_write.cpu.registers._pc if traced_write.cpu else 0
        flag_writes.append((traced_write.cpu.total_cycles, pc, value))
    return original_write(address, value)

def traced_read(address):
    result = original_read(address)
    if address == 0xFF85:
        pc = traced_read.cpu.registers._pc if traced_read.cpu else 0
        flag_reads.append((traced_read.cpu.total_cycles, pc, result))
    return result


def trace_vblank_flag():
    """Trace VBlank flag usage"""
    print("="*70)
    print("VBLANK FLAG (0xFF85) TRACE")
    print("="*70)

    cpu = CPU()

    # Patch
    global original_write, original_read
    original_write = cpu.memory.write_byte
    original_read = cpu.memory.read_byte
    traced_write.cpu = cpu
    traced_read.cpu = cpu
    cpu.memory.write_byte = traced_write
    cpu.memory.read_byte = traced_read

    cpu.memory.load_rom_file(TETRIS_ROM)

    print("\nRunning for 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    # Analyze writes
    print(f"\n" + "="*70)
    print("FLAG WRITES (0xFF85)")
    print("="*70)

    print(f"\nTotal writes: {len(flag_writes)}")

    if flag_writes:
        print(f"\nFirst 30 writes:")
        for i, (cycles, pc, value) in enumerate(flag_writes[:30]):
            print(f"  {i+1:3d}. Cycle {cycles:8d} from PC 0x{pc:04X}: wrote 0x{value:02X}")

        # Group by value
        writes_1 = [w for w in flag_writes if w[2] == 1]
        writes_0 = [w for w in flag_writes if w[2] == 0]

        print(f"\nWrites by value:")
        print(f"  Writes of 0x01: {len(writes_1)}")
        print(f"  Writes of 0x00: {len(writes_0)}")

        # Check PC patterns
        write_pcs = {}
        for cycles, pc, value in flag_writes:
            if pc not in write_pcs:
                write_pcs[pc] = []
            write_pcs[pc].append(value)

        print(f"\nWrites by PC:")
        for pc, values in sorted(write_pcs.items()):
            value_counts = {v: values.count(v) for v in set(values)}
            print(f"  0x{pc:04X}: {len(values)} writes - {value_counts}")

    # Analyze reads
    print(f"\n" + "="*70)
    print("FLAG READS (0xFF85)")
    print("="*70)

    print(f"\nTotal reads: {len(flag_reads)}")

    if flag_reads:
        # Check read locations
        read_pcs = {}
        for cycles, pc, value in flag_reads:
            if pc not in read_pcs:
                read_pcs[pc] = []
            read_pcs[pc].append(value)

        print(f"\nReads by PC:")
        for pc, values in sorted(read_pcs.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            value_counts = {v: values.count(v) for v in set(values)}
            print(f"  0x{pc:04X}: {len(values)} reads - {value_counts}")

        # Check timing between write and read
        if flag_writes and flag_reads:
            print(f"\nTiming analysis:")

            # Find a write->read pair
            for i, (write_cycle, write_pc, write_val) in enumerate(flag_writes[:5]):
                # Find next read after this write
                next_reads = [r for r in flag_reads if r[0] > write_cycle and r[0] < write_cycle + 1000]

                if next_reads:
                    read_cycle, read_pc, read_val = next_reads[0]
                    delta = read_cycle - write_cycle
                    print(f"\n  Write {i+1}: Cycle {write_cycle} wrote 0x{write_val:02X}")
                    print(f"    Next read: Cycle {read_cycle} read 0x{read_val:02X} (delta: {delta} cycles)")

                    if write_val != read_val:
                        print(f"    ⚠️  Value changed between write and read!")

    # Check VBlank interrupt handler
    print(f"\n" + "="*70)
    print("VBLANK INTERRUPT HANDLER CHECK")
    print("="*70)

    # VBlank handler should be at 0x0040 -> jumps to 0x017E
    print(f"\nVBlank vector (0x0040):")
    for i in range(3):
        byte = cpu.memory.read_byte(0x0040 + i)
        print(f"  0x{0x0040+i:04X}: 0x{byte:02X}")

    # Handler code
    print(f"\nVBlank handler (0x017E):")
    for i in range(20):
        byte = cpu.memory.read_byte(0x017E + i)
        print(f"  0x{0x017E+i:04X}: 0x{byte:02X}")

    # Check if handler writes to 0xFF85
    handler_writes = [w for w in flag_writes if 0x017E <= w[1] <= 0x01A0]

    if handler_writes:
        print(f"\n✅ VBlank handler DOES write to 0xFF85")
        print(f"   {len(handler_writes)} writes from handler")
    else:
        print(f"\n❌ VBlank handler does NOT write to 0xFF85")
        print(f"   Flag must be set elsewhere")


if __name__ == '__main__':
    trace_vblank_flag()
