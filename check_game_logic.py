"""
Check what game logic runs after VBlank synchronization
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

def check_game_logic():
    """Check what the game is doing"""
    print("="*70)
    print("CHECKING GAME LOGIC EXECUTION")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 1.5M cycles...")
    while cpu.total_cycles < 1_500_000:
        cpu.step()

    # Wait for VBlank flag to be set
    print("\nWaiting for VBlank flag to be set...")
    timeout = cpu.total_cycles + 100_000
    while cpu.memory.read_byte(0xFF85) == 0 and cpu.total_cycles < timeout:
        cpu.step()

    if cpu.memory.read_byte(0xFF85) != 0:
        print(f"  Flag set at cycle {cpu.total_cycles:,}")
    else:
        print(f"  Timeout - flag never set")
        return

    # Now trace execution through the game logic
    print("\nTracing game logic after flag check...")

    execution_trace = []
    call_stack = []

    for i in range(1000):
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        # Track calls and returns
        if opcode == 0xCD:  # CALL
            low = cpu.memory.read_byte(pc + 1)
            high = cpu.memory.read_byte(pc + 2)
            target = (high << 8) | low
            call_stack.append((pc, target))
            execution_trace.append(f"PC=0x{pc:04X}: CALL 0x{target:04X}")
        elif opcode == 0xC9:  # RET
            if call_stack:
                execution_trace.append(f"PC=0x{pc:04X}: RET")
        elif pc in [0x02F3, 0x02F5]:  # Flag clear and jump
            low = cpu.memory.read_byte(pc + 1)
            high = cpu.memory.read_byte(pc + 2)
            target = (high << 8) | low
            execution_trace.append(f"PC=0x{pc:04X}: JP 0x{target:04X}")

        cpu.step()

        # Stop if we hit the VBlank wait loop again
        if pc == 0x02ED:
            execution_trace.append(f"PC=0x{pc:04X}: Back to VBlank wait loop")
            break

    print(f"\nExecution trace (first {len(execution_trace)} significant instructions):")
    for trace in execution_trace[:50]:
        print(f"  {trace}")

    if len(execution_trace) > 50:
        print(f"  ... ({len(execution_trace) - 50} more)")

    # Check calls made
    print(f"\nCalls made:")
    unique_calls = set(target for _, target in call_stack)
    for target in sorted(unique_calls):
        count = sum(1 for _, t in call_stack if t == target)
        print(f"  0x{target:04X}: called {count} times")

    # Check RAM locations that might be game state
    print(f"\nChecking game state RAM:")

    # Common RAM locations for game state
    locations = [
        (0xC000, "C000"),
        (0xC001, "C001"),
        (0xC002, "C002"),
        (0xC003, "C003"),
        (0xC004, "C004"),
        (0xC005, "C005"),
        (0xFF80, "FF80 (HRAM)"),
        (0xFF81, "FF81"),
        (0xFF82, "FF82"),
        (0xFF83, "FF83"),
        (0xFF84, "FF84"),
    ]

    for addr, name in locations:
        value = cpu.memory.read_byte(addr)
        print(f"  [0x{name}] = 0x{value:02X}")

    # Check if game has set up sprites in OAM source
    print(f"\nChecking OAM source data (0xC000-0xC09F):")

    oam_bytes = [cpu.memory.read_byte(0xC000 + i) for i in range(160)]
    non_zero = sum(1 for b in oam_bytes if b != 0)

    print(f"  Non-zero bytes: {non_zero}/160")

    if non_zero > 0:
        print(f"  First 20 bytes:")
        for i in range(20):
            print(f"    [0x{0xC000+i:04X}] = 0x{oam_bytes[i]:02X}")


if __name__ == '__main__':
    check_game_logic()
