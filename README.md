# SnekBoy

A Game Boy (DMG) emulator written in Python, implementing the complete Sharp LR35902 CPU instruction set and core hardware components.

<img width="462" height="176" alt="Sb" src="https://github.com/user-attachments/assets/cd4fc784-ecff-4798-a9d1-94cecba4cec5" />

## Overview

SnekBoy is a Game Boy emulator that aims to accurately emulate the original Game Boy hardware, including CPU, PPU (graphics), timer system, joypad input, and interrupt handling. The emulator passes Blargg's cpu_instrs and instr_timing test suites. While core systems are functional, there are known bugs preventing full game compatibility that are currently being investigated.

<img width="306" height="276" alt="tt" src="https://github.com/user-attachments/assets/95abb3ab-3b99-4bba-a482-7d5468d314d6" />

## Features

- Complete CPU emulation (all 512 opcodes)
- Pixel Processing Unit (PPU) with background, window, and sprite rendering
- Accurate timing system (DIV, TIMA, TMA, TAC registers)
- Full interrupt support (VBlank, STAT, Timer, Serial, Joypad)
- Joypad input with keyboard mapping
- Boot ROM simulation
- Execution tracing for debugging
- Pygame-based display output

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/snekboy.git
cd snekboy

# Install dependencies
pip install pygame
```

### Running Games

```bash
# Run with a ROM file
python -m src.emulator path/to/game.gb

# Run without tracing (better performance)
python -m src.emulator path/to/game.gb --no-trace

# Run test pattern (no ROM required)
python -m src.emulator
```

### Controls

**Game Buttons:**
- A: A key
- B: S key
- Start: Z key
- Select: X key

**D-Pad:**
- Up: I key
- Down: K key
- Left: J key
- Right: L key

**System:**
- Quit: ESC key

## Project Structure

```
snekboy/
├── src/                        # Source code
│   ├── cpu.py                  # CPU emulation core
│   ├── cpu_decoder.py          # Instruction decoder
│   ├── instructions_impl.py    # Instruction implementations
│   ├── memory.py               # Memory management and I/O
│   ├── ppu.py                  # Graphics rendering
│   ├── joypad.py               # Input handling
│   ├── timer.py                # Timer system
│   ├── tracer.py               # Execution tracing
│   ├── display.py              # Display output
│   ├── emulator.py             # Main emulator loop
│   ├── registers.py            # CPU registers
│   ├── opcodes.py              # Opcode definitions
│   ├── gameboy_doctor.py       # Test integration
│   └── utils.py                # Utility functions
│
├── tests/                      # Test suite
│   ├── README.md               # Test documentation
│   ├── run_unit_tests.py       # Component tests
│   ├── run_blargg_tests.py     # Blargg test ROMs
│   └── diagnostic_tools.py     # Debugging tools
│
├── docs/                       # Documentation
│   ├── gameboy_reference.md    # Hardware reference
│   ├── development.md          # Implementation details
│   ├── tracing.md              # Tracing guide
│   └── opcode_reference.md     # Opcode quick reference
│
├── test_roms/                  # Test ROM files
├── tools/                      # Development tools
│   └── disassemble_rom.py      # ROM disassembler
│
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## Components

### CPU (src/cpu.py)
Emulates the Sharp LR35902 processor, a modified Z80:
- All 256 standard opcodes (0x00-0xFF)
- All 256 CB-prefixed opcodes (0xCB00-0xCBFF)
- 8-bit and 16-bit arithmetic operations
- Bit manipulation instructions (SET, RES, BIT, SWAP)
- Control flow (JP, JR, CALL, RET, RST)
- Stack operations (PUSH, POP)
- Special instructions (DAA, HALT, STOP, EI, DI, RETI)
- Accurate flag handling (Zero, Negative, Half-carry, Carry)
- Cycle-accurate timing

### Memory (src/memory.py)
Manages the 64KB address space:
- ROM banking support (0x0000-0x7FFF)
- VRAM (0x8000-0x9FFF) with PPU access restrictions
- Work RAM (0xC000-0xDFFF)
- OAM sprite table (0xFE00-0xFE9F)
- I/O registers (0xFF00-0xFF7F)
- High RAM (0xFF80-0xFFFE)
- Boot ROM overlay simulation
- DMA transfer support

### PPU (src/ppu.py)
Picture Processing Unit for graphics:
- 160x144 pixel display
- Background layer with scrolling (SCX, SCY)
- Window layer overlay
- Sprite rendering (40 sprites, 8x8 or 8x16 mode)
- 4 grayscale colors with palette support
- PPU modes: OAM Search, Pixel Transfer, HBlank, VBlank
- Cycle-accurate timing (456 T-cycles per scanline)
- STAT and VBlank interrupts

### Timer (src/cpu.py _update_timers)
Implements the Game Boy timer system:
- DIV register (0xFF04): 16384 Hz divider
- TIMA register (0xFF05): Programmable timer counter
- TMA register (0xFF06): Timer modulo/reload value
- TAC register (0xFF07): Timer control (enable and frequency)
- Four frequency modes: 4096 Hz, 262144 Hz, 65536 Hz, 16384 Hz
- Falling-edge detection for TIMA increments
- Overflow behavior with 1-cycle delay
- Timer interrupt generation

### Joypad (src/joypad.py)
Input handling via P1 register (0xFF00):
- 8 buttons: A, B, Start, Select, Up, Down, Left, Right
- Button group selection (action buttons / d-pad)
- Joypad interrupt on button press
- Keyboard event mapping

### Display (src/display.py)
Graphics output using Pygame:
- 480x432 window (3x scaling from 160x144)
- 60 FPS frame limiting
- Game Boy color palette
- Keyboard input handling

### Tracer (src/tracer.py)
Execution tracing for debugging:
- LCDC register writes (LCD on/off)
- VRAM writes
- LY register reads
- DMA transfers
- VBlank interrupts
- State snapshots
- Configurable sampling to minimize overhead

## Dependencies

- Python 3.8 or higher
- pygame >= 2.0.0

```bash
pip install pygame
```

## Workflow

### Execution
```bash
# Standard execution
python -m src.emulator path/to/rom.gb

# With tracing disabled
python -m src.emulator path/to/rom.gb --no-trace

# Test pattern (no ROM)
python -m src.emulator
```

### Testing
```bash
# Run all unit tests
python tests/run_unit_tests.py all

# Run specific component tests
python tests/run_unit_tests.py cpu
python tests/run_unit_tests.py timer
python tests/run_unit_tests.py joypad

# Run Blargg test ROMs
python tests/run_blargg_tests.py

# Download test ROMs (first time)
python tests/download_test_roms.py
```

### Debugging
```bash
# Check game state at specific cycle
python tests/diagnostic_tools.py tetris_state

# Trace interrupt behavior
python tests/diagnostic_tools.py trace_interrupts

# Monitor VBlank interrupts
python tests/diagnostic_tools.py check_vblank

# Analyze polling loops
python tests/diagnostic_tools.py polling_loop
```

Execution traces are written to `tracing/tracing.txt` when enabled. See `docs/tracing.md` for details.

## References

### Game Boy Documentation
- [Pan Docs](https://gbdev.io/pandocs/) - Complete Game Boy technical reference
- [Game Boy CPU Manual](http://marc.rawer.de/Gameboy/Docs/GBCPUman.pdf) - Official CPU documentation
- [GBEDG](https://github.com/Hacktix/GBEDG) - Edge case and timing documentation
- [Opcode Table](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html) - Instruction reference

### Test ROMs
- [Blargg's Test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/) - CPU and timing tests by Shay Green
  - cpu_instrs.gb - CPU instruction test suite
  - instr_timing.gb - Instruction timing verification
  - mem_timing.gb - Memory timing tests
  - interrupt_time.gb - Interrupt timing tests

- [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite) - Comprehensive hardware tests by Gekkio

- [Gameboy Doctor](https://github.com/robert/gameboy-doctor) - CPU test integration tool by Robert Heaton

### Reference Emulators
- [BGB](https://bgb.bircd.org/) - Windows debugger and emulator
- [SameBoy](https://sameboy.github.io/) - Highly accurate, hardware-verified emulator
- [Gambatte](https://github.com/sinamas/gambatte) - Cycle-accurate emulator

### Community
- [r/EmuDev](https://www.reddit.com/r/EmuDev/) - Emulator development community
- [GBDev](https://gbdev.io/) - Game Boy development resources

## Test ROM Credits

This emulator uses test ROMs created by the Game Boy development community:

- **Blargg's Test ROMs** by Shay Green (blargg) - CPU instruction and timing tests
- **Mooneye Test Suite** by Joonas Javanainen (Gekkio) - Hardware accuracy tests
- **Gameboy Doctor** by Robert Heaton - CPU test framework

Special thanks to all contributors to the Game Boy emulation and homebrew community.

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome. Please:
1. Read `docs/development.md` for implementation details
2. Run tests to verify current state
3. Check known issues before starting work
4. Submit pull requests with clear descriptions

## Development Status

Current version: 1.0.0 (Beta)

Core systems are complete and functional. The emulator passes standard test suites (Blargg's cpu_instrs and instr_timing). Game compatibility is limited due to bugs in stage transition handling that are being researched. Tetris boots and navigates menus but crashes when loading stages. Audio (APU) and Memory Bank Controllers (MBC) are not yet implemented.

For detailed implementation status and known issues, see `docs/development.md`.
