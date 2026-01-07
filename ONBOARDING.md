# SnekBoy Emulator - Developer Onboarding

Welcome! This document will get you up to speed quickly.

## 5-Minute Quick Start

### What is SnekBoy?
A Game Boy (DMG) emulator in Python. Currently passes Blargg tests 01-02, displays graphics, and has working input.

### Current Status
- ✅ **Working**: CPU, Timer, Interrupts, PPU, Joypad, Tetris displays
- ❌ **Not Working**: Blargg test 03 (times out), Audio, MBCs, Tetris gameplay not fully tested

### Run It Now
```bash
# Install dependencies
pip install pygame

# Run Tetris
python src/emulator.py

# Run tests
python tests/run_unit_tests.py all
python tests/run_blargg_tests.py
```

---

## Read These First (10 minutes)

### 1. PROJECT_STATUS.md (5 min)
- **What it contains**: Current features, known bugs, architecture overview
- **When to read**: Right now, before touching code
- **Key sections**: "What Works", "Known Bugs", "Common Pitfalls"

### 2. DEBUGGING_SESSION.md (5 min - skim)
- **What it contains**: Every bug found and fixed, with explanations
- **When to read**: When you hit a bug or need context on a fix
- **Key sections**: "Resolved & Working" for understanding past fixes

---

## Your First Task: Fix Blargg Test 03

### The Problem
Blargg test 03 (OP SP,HL) times out at 30M cycles instead of completing.

### What We Know
- Tests `ADD SP,e` and `LD HL,SP+e` instructions
- Likely a flag calculation bug (H or C flag)
- See `DEBUGGING_SESSION.md` → "Issue 1: Blargg Test 03 Timeout"

### How to Start
```bash
# 1. Run the test to see current behavior
python tests/run_blargg_tests.py

# 2. Look at test 03 investigation notes
cat docs/test_03_investigation_summary.md

# 3. Check the ADD SP,e implementation
grep -n "ADD SP" src/instructions_impl.py

# 4. Create a focused test
# (see tests/test_add_sp_*.py for examples)
```

### Where to Look
- `src/instructions_impl.py` - Instruction implementations
- `src/cpu.py` - Flag calculations
- Tests 01-02 pass, so those instructions are correct (reference!)

---

## Project Structure

```
snekboy/
├── src/
│   ├── cpu.py              # CPU core, decode, execute loop
│   ├── instructions_impl.py # All 512 instruction implementations
│   ├── registers.py        # Register file, flags
│   ├── memory.py          # Memory map, I/O, timer
│   ├── ppu.py             # Graphics (PPU/LCD)
│   ├── joypad.py          # Input handling
│   ├── display.py         # Pygame window
│   └── emulator.py        # Main entry point
├── tests/
│   ├── run_unit_tests.py   # Run component tests
│   ├── run_blargg_tests.py # Run Blargg test ROMs
│   ├── diagnostic_tools.py # Debug helpers
│   └── README.md          # Test suite docs
├── docs/
│   ├── ppu_implementation.md
│   ├── timer_implementation_status.md
│   ├── joypad_implementation.md
│   └── GENERAL_GB_REFERENCE.md
├── PROJECT_STATUS.md       # ⭐ Start here
├── DEBUGGING_SESSION.md    # ⭐ Read when stuck
└── ONBOARDING.md          # ⭐ This file
```

---

## Critical Things to Know

### 1. T-cycles vs M-cycles
```python
# ALWAYS remember:
# - Opcode table has T-cycles (4 MHz clock)
# - Timers use M-cycles (1 MHz clock)
# - 1 M-cycle = 4 T-cycles

m_cycles = t_cycles // 4
self._update_timers(m_cycles)  # Correct!
```

### 2. F Register Masking
```python
# F register lower 4 bits MUST be 0
value = value & 0xF0  # Always mask when loading F
```

### 3. Interrupt Timing
```python
# EI: 1-instruction delay (uses counter)
self._ei_pending = 2  # Counts down to 0

# RETI: Immediate enable (no delay)
self.ime = True
```

### 4. HALT Behavior
```python
# HALT doesn't stop execution!
# Must keep calling step() for timers/interrupts
while cpu.total_cycles < max:
    cpu.step()  # Keep calling even when halted!
```

---

## Common Tasks

### Add a New Instruction
1. Find opcode in `src/cpu.py` OPCODES table
2. Implement in `src/instructions_impl.py`
3. Create unit test in `tests/`
4. Run: `python tests/run_blargg_tests.py`

### Debug a Failing Game
```bash
# Use diagnostic tools
python tests/diagnostic_tools.py tetris_state

# Or create a trace script
python tests/trace_my_issue.py
```

### Run Specific Tests
```bash
# Unit tests
python tests/run_unit_tests.py cpu

# Blargg tests
python tests/run_blargg_tests.py

# Diagnostic
python tests/diagnostic_tools.py trace_interrupts
```

---

## Development Workflow

### Before You Code
1. ✅ Read PROJECT_STATUS.md
2. ✅ Check if bug is in known issues
3. ✅ Run tests to confirm current state

### While Coding
1. Make small changes
2. Run unit tests frequently: `python tests/run_unit_tests.py all`
3. Use diagnostic tools for tracing
4. Compare with Pan Docs (see Resources below)

### Before You Commit
1. ✅ All unit tests pass
2. ✅ Blargg tests don't regress (01-02 still pass)
3. ✅ Update PROJECT_STATUS.md if needed
4. ✅ Update DEBUGGING_SESSION.md if you fixed a bug

---

## Essential Resources

### Game Boy Technical Docs
- [Pan Docs](https://gbdev.io/pandocs/) - **THE BIBLE** - Read this!
- [GBEDG](https://github.com/Hacktix/GBEDG) - Timing edge cases
- [Opcode Table](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html)

### Test ROMs
- [Blargg's Test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/)
- [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite)

### Community
- [r/EmuDev Reddit](https://www.reddit.com/r/EmuDev/)
- Discord: EmuDev, GBDev servers

### Reference Emulators (for comparison)
- **BGB** - Windows, best debugger
- **SameBoy** - Most accurate
- **Gambatte** - Cycle-accurate

---

## Debugging Tips

### Test ROM Gives Error Code
1. Check `DEBUGGING_SESSION.md` for that test
2. Look at serial output to see which sub-test
3. Create focused test for that instruction
4. Compare flag/register behavior with reference emulator

### Game Doesn't Progress
1. Run diagnostic: `python tests/diagnostic_tools.py tetris_state`
2. Check if stuck in loop (same PC repeatedly)
3. Check interrupt state (IME, IE, IF)
4. Trace execution for a few hundred instructions

### "Works in BGB, not here"
1. Compare register states at same PC
2. Compare memory at key addresses
3. Check cycle count timing
4. Look for missing edge cases in Pan Docs

---

## Next Priority Tasks

### Immediate (Get test 03 passing)
1. Debug `ADD SP,e` flag calculations
2. Debug `LD HL,SP+e` flag calculations
3. Verify instruction cycle counts
4. Compare with reference emulator

### Short Term (Complete Blargg suite)
1. Pass tests 04-11
2. Test Tetris gameplay thoroughly
3. Try other simple ROMs (Dr. Mario, etc.)

### Long Term (Full Compatibility)
1. Implement MBC1/MBC3
2. Add Audio APU
3. Implement save states
4. Handle more PPU edge cases

---

## Getting Help

### When Stuck
1. Check `DEBUGGING_SESSION.md` - someone may have hit this before
2. Check Pan Docs - hardware behavior may be non-obvious
3. Search r/EmuDev - very helpful community
4. Compare with reference emulator

### Red Flags (You're probably wrong if...)
- "The test ROM must be buggy" - No, test ROMs are correct
- "I'll just skip this edge case" - Edge cases matter!
- "Close enough" for flag calculations - Must be exact
- Changing timing randomly - Understand the root cause first

---

## Final Checklist

Before you start coding, make sure you've:
- ✅ Read PROJECT_STATUS.md
- ✅ Skimmed DEBUGGING_SESSION.md
- ✅ Run tests to see current state
- ✅ Identified which file to modify
- ✅ Have Pan Docs open in browser

Now you're ready! Good luck, and welcome to the team.

**First PR goal: Get Blargg test 03 passing!**
