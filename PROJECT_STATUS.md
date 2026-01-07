# SnekBoy - Game Boy Emulator Project Status

## Quick Start for New Developers

### What Works
- ✅ Core CPU instruction set (all opcodes implemented)
- ✅ Timer system (DIV, TIMA, TMA, TAC registers)
- ✅ Interrupt handling (VBlank, Timer, Joypad interrupts)
- ✅ PPU/Display (renders graphics, LCD modes, sprites, background)
- ✅ Joypad input (all buttons mapped)
- ✅ Memory management (ROM, RAM, I/O registers)
- ✅ Blargg cpu_instrs tests 01-02 (PASS)

### What Doesn't Work Yet
- ❌ Blargg cpu_instrs test 03 (OP SP,HL) - times out
- ❌ Audio (not implemented)
- ❌ MBC (Memory Bank Controllers) - only basic ROM loading
- ❌ Save states
- ❌ Serial/Link cable emulation

---

## Recent Development (Latest Session)

### Implemented Features

#### 1. **Joypad/Input System** (COMPLETE)
- Full P1 register (0xFF00) implementation
- Button group selection (buttons vs d-pad)
- Inverted logic (0=pressed, 1=released)
- Joypad interrupt triggering
- Key mappings:
  - Buttons: A='A', B='S', Start='Z', Select='X'
  - D-Pad: Up='I', Down='K', Left='J', Right='L'

**Files:**
- `src/joypad.py` - Complete joypad controller
- `src/memory.py` - P1 register integration
- `src/display.py` - Keyboard event handling
- `src/emulator.py` - Joypad connection to main loop

#### 2. **Critical Interrupt Bugs Fixed**

##### Bug A: EI (Enable Interrupts) Instruction Delay
**Problem:** EI enables interrupts AFTER the next instruction executes (1-instruction delay), but implementation was enabling them immediately.

**Impact:** Interrupts fired before the delay instruction completed, breaking Tetris game progression.

**Fix:** Changed `_ei_pending` from boolean to integer counter:
- EI sets `_ei_pending = 2`
- Each step() decrements: 2 → 1 (execute delay instruction) → 0 (enable IME)

**File:** `src/instructions_impl.py:543`

##### Bug B: RETI (Return from Interrupt) Not Enabling Interrupts
**Problem:** RETI instruction had a TODO comment and didn't re-enable interrupts (just had `pass`).

**Impact:** Game got stuck in polling loops after first interrupt because IME stayed False.

**Fix:** Added:
- `self.ime = True` - Re-enable interrupts immediately
- `self._ei_pending = 0` - Cancel any pending EI

**File:** `src/instructions_impl.py:525-528`

---

## Known Bugs & Issues

### Critical
- **Blargg Test 03 Timeout**: Test 03 (OP SP,HL) doesn't complete within 30M cycles
  - Likely related to `ADD SP,e` or `LD HL,SP+e` instruction implementation
  - May be flag calculation or timing issue
  - See `docs/test_03_investigation_summary.md` for investigation details

### Medium Priority
- **No Audio**: Audio APU not implemented
- **No MBC Support**: Can only run simple ROMs without bank switching
- **No Save Support**: Battery-backed RAM not implemented

### Low Priority
- **No Serial Link**: Link cable emulation not implemented
- **No Save States**: Can't save/load emulator state

---

## Test Suite Status

### Blargg cpu_instrs Tests
| Test | Name | Status | Notes |
|------|------|--------|-------|
| 01 | special | ✅ PASS | Special instructions working |
| 02 | interrupts | ✅ PASS | Timer & interrupt handling correct |
| 03 | op sp,hl | ❌ FAIL | Times out, needs investigation |
| 04-11 | ... | ⏸️ PENDING | Blocked by test 03 |

### Manual Tests
- ✅ Tetris ROM loads and displays copyright screen
- ✅ Graphics render correctly (background, sprites)
- ⏸️ Tetris gameplay not tested yet (blocked on test 03)

---

## Architecture Overview

### Core Components
```
src/
├── cpu.py              # CPU core, instruction decoder, execution loop
├── instructions_impl.py # All instruction implementations
├── registers.py        # Register file, flags
├── memory.py          # Memory map, I/O registers, timer
├── ppu.py             # Picture Processing Unit (graphics)
├── joypad.py          # Joypad controller
├── display.py         # Pygame display/input handling
└── emulator.py        # Main emulator loop
```

### Memory Map (Standard Game Boy)
```
0x0000-0x3FFF  ROM Bank 0 (16KB)
0x4000-0x7FFF  ROM Bank 1-N (16KB switchable)
0x8000-0x9FFF  VRAM (8KB)
0xA000-0xBFFF  External RAM (8KB)
0xC000-0xDFFF  Work RAM (8KB)
0xE000-0xFDFF  Echo RAM (mirror of 0xC000-0xDDFF)
0xFE00-0xFE9F  OAM (Sprite attributes)
0xFEA0-0xFEFF  Unusable
0xFF00-0xFF7F  I/O Registers
0xFF80-0xFFFE  High RAM (HRAM)
0xFFFF         IE (Interrupt Enable)
```

### Critical I/O Registers
```
0xFF00  P1/JOYP   Joypad
0xFF04  DIV       Divider register (16384 Hz)
0xFF05  TIMA      Timer counter
0xFF06  TMA       Timer modulo
0xFF07  TAC       Timer control
0xFF0F  IF        Interrupt flags
0xFF40  LCDC      LCD control
0xFF41  STAT      LCD status
0xFF44  LY        LCD Y-coordinate
0xFFFF  IE        Interrupt enable
```

---

## Key Implementation Details

### Timer System
- DIV increments every 256 T-cycles (64 M-cycles)
- TIMA increments based on TAC frequency setting
- Overflow sets bit 2 in IF register (0xFF0F)
- 4-cycle delay between overflow and reload from TMA
- Edge detection on TAC writes can cause spurious ticks

**Critical:** Use M-cycles for timer updates, not T-cycles!
- 1 M-cycle = 4 T-cycles
- Instruction timings in opcode table are T-cycles
- Must convert: `m_cycles = t_cycles // 4`

### Interrupt System
- Priority order: VBlank > LCD > Timer > Serial > Joypad
- IME (Interrupt Master Enable) flag controls global enable
- EI instruction has 1-instruction delay before enabling
- RETI re-enables interrupts immediately (no delay)
- Interrupts can wake CPU from HALT state

### PPU/Graphics
- 4 LCD modes: HBlank (0), VBlank (1), OAM Search (2), Transfer (3)
- Screen: 160x144 pixels
- VBlank happens at scanline 144
- Supports background, window, sprites (8x8 or 8x16)
- 4 shades of gray (0-3)

---

## Running Tests

### Blargg Tests
```bash
python tests/test_with_blargg.py
```

### Unit Tests
```bash
# Interrupt instruction tests
python tests/test_interrupt_instructions.py

# Joypad tests
python tests/test_joypad.py

# All organized tests
python tests/run_tests.py
```

### Run Tetris
```bash
python src/emulator.py
```

Controls:
- A/B/Start/Select: A, S, Z, X
- D-Pad (Up/Down/Left/Right): I, K, J, L
- Quit: ESC

---

## Dependencies
- Python 3.8+
- pygame (for display/input)

---

## Documentation
- `PROJECT_STATUS.md` - This file, current status and overview
- `DEBUGGING_SESSION.md` - Complete debugging history with fixes
- `docs/barebone_emulation_roadmap.md` - General Game Boy emulation guide
- `docs/ppu_implementation.md` - PPU/graphics implementation details
- `docs/timer_implementation_status.md` - Timer system implementation
- `docs/joypad_implementation.md` - Joypad system implementation

---

## Next Steps for Development

### Immediate Priority
1. Debug Blargg test 03 (OP SP,HL)
   - Focus on `ADD SP,e` and `LD HL,SP+e` instructions
   - Verify flag calculations (especially H and C flags)
   - Check instruction timing

### Short Term
2. Complete remaining Blargg cpu_instrs tests (04-11)
3. Test Tetris gameplay with joypad input
4. Verify more commercial ROMs work

### Long Term
4. Implement MBC1/MBC3 for more ROM compatibility
5. Add Audio APU (channels 1-4)
6. Implement save states
7. Add debugger/disassembler UI

---

## Common Pitfalls & Gotchas

1. **T-cycles vs M-cycles**: Always verify which unit timing code expects
2. **F register masking**: Lower 4 bits must always be 0
3. **HALT behavior**: Must continue stepping to update timers
4. **Interrupt timing**: EI has delay, RETI doesn't
5. **Timer edge cases**: DIV writes reset internal counter, TAC writes trigger edge detection
6. **PPU timing**: Must be cycle-accurate for many games
7. **Joypad logic**: Inverted (0=pressed, 1=released)

---

## Credits & Resources

### Essential Reading
- [Pan Docs](https://gbdev.io/pandocs/) - Complete Game Boy technical reference
- [GBEDG](https://github.com/Hacktix/GBEDG) - Accurate timing documentation
- [Game Boy Opcode Table](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html)
- [r/EmuDev](https://www.reddit.com/r/EmuDev/) - Community support

### Test ROMs
- [Blargg's Test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/)
- [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite)
