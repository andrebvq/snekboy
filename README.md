# SnekBoy - Game Boy Emulator

A Game Boy (DMG) emulator written in Python.

## Quick Start

```bash
# Install dependencies
pip install pygame

# Run Tetris
python src/emulator.py

# Run tests
python tests/run_unit_tests.py all
python tests/run_blargg_tests.py
```

**Controls:**
- A/B/Start/Select: A, S, Z, X
- D-Pad (Up/Down/Left/Right): I, K, J, L
- Quit: ESC

---

## 📚 Documentation Guide

### New Developer? Start Here

1. **[ONBOARDING.md](ONBOARDING.md)** (10 min read)
   - Quick overview and first steps
   - What to read, what to skip
   - Your first task: Fix Blargg test 03

2. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** (5 min read)
   - Current status: what works, what doesn't
   - Known bugs and issues
   - Architecture overview
   - **READ THIS BEFORE CODING**

3. **[DEBUGGING_SESSION.md](DEBUGGING_SESSION.md)** (reference)
   - Complete history of all debugging
   - Every bug found and how it was fixed
   - Read when you encounter a bug

### Additional Documentation

- **[tests/README.md](tests/README.md)** - Test suite organization
- **[docs/GENERAL_GB_REFERENCE.md](docs/GENERAL_GB_REFERENCE.md)** - Game Boy hardware reference
- **[docs/ppu_implementation.md](docs/ppu_implementation.md)** - PPU/graphics details
- **[docs/timer_implementation_status.md](docs/timer_implementation_status.md)** - Timer system
- **[docs/joypad_implementation.md](docs/joypad_implementation.md)** - Input handling

---

## Current Status

### ✅ Working
- Core CPU instruction set (all 512 opcodes)
- Timer system (DIV, TIMA, TMA, TAC)
- Interrupt handling (EI/DI/RETI with correct timing)
- PPU/Display (background, sprites, LCD modes)
- Joypad input (all buttons)
- Blargg cpu_instrs tests 01-02 **PASS**

### ❌ Not Working Yet
- Blargg test 03 (OP SP,HL) - **NEXT PRIORITY**
- Audio (not implemented)
- MBCs (only basic ROM loading)
- Save states

---

## Project Structure

```
snekboy/
├── README.md              ← You are here
├── ONBOARDING.md         ← Start here if new
├── PROJECT_STATUS.md     ← Current status & bugs
├── DEBUGGING_SESSION.md  ← Bug fix history
│
├── src/                  ← Source code
│   ├── cpu.py           # CPU core
│   ├── instructions_impl.py  # All instructions
│   ├── memory.py        # Memory & I/O
│   ├── ppu.py           # Graphics
│   ├── joypad.py        # Input
│   └── emulator.py      # Main entry
│
├── tests/                ← Test suite
│   ├── README.md        # Test organization
│   ├── run_unit_tests.py     # Component tests
│   ├── run_blargg_tests.py   # Blargg test ROMs
│   └── diagnostic_tools.py   # Debug helpers
│
└── docs/                 ← Technical docs
    ├── GENERAL_GB_REFERENCE.md  # Hardware reference
    ├── ppu_implementation.md
    ├── timer_implementation_status.md
    └── joypad_implementation.md
```

---

## Running Tests

### Unit Tests
```bash
# All tests
python tests/run_unit_tests.py all

# Specific component
python tests/run_unit_tests.py cpu
python tests/run_unit_tests.py timer
python tests/run_unit_tests.py joypad
```

### Blargg Test ROMs
```bash
# Download test ROMs first (one-time)
python tests/download_test_roms.py

# Run tests
python tests/run_blargg_tests.py
```

### Diagnostic Tools
```bash
# Check game state
python tests/diagnostic_tools.py tetris_state

# Trace interrupts
python tests/diagnostic_tools.py trace_interrupts

# Monitor VBlank
python tests/diagnostic_tools.py check_vblank
```

---

## Next Development Priorities

1. **Fix Blargg Test 03** (OP SP,HL)
   - Likely flag calculation in `ADD SP,e` or `LD HL,SP+e`
   - See `DEBUGGING_SESSION.md` → "Issue 1"

2. **Complete Blargg Suite** (Tests 04-11)

3. **Test Tetris Gameplay**

4. **Add MBC Support**

---

## Dependencies

- Python 3.8+
- pygame (for display)

```bash
pip install pygame
```

---

## Resources

- [Pan Docs](https://gbdev.io/pandocs/) - Complete Game Boy reference
- [GBEDG](https://github.com/Hacktix/GBEDG) - Timing documentation
- [Opcode Table](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html)
- [Blargg Test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/)
- [r/EmuDev](https://www.reddit.com/r/EmuDev/) - Community support

---

## License

MIT License - See LICENSE file for details

---

## Contributing

Before starting:
1. Read [ONBOARDING.md](ONBOARDING.md)
2. Read [PROJECT_STATUS.md](PROJECT_STATUS.md)
3. Run tests to verify current state
4. Check known issues before starting work

**First contribution goal: Get Blargg test 03 passing!**
