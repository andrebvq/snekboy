# Development Documentation

Comprehensive development status, implementation details, and debugging information for the SnekBoy Game Boy emulator.

## Implementation Status

### Completed Components

| Component | Completeness | Status |
|-----------|--------------|--------|
| CPU Core | 100% | All opcodes implemented |
| Memory Management | 100% | 64KB address space, I/O registers |
| PPU (Graphics) | 95% | Background, window, sprites working |
| Joypad Input | 100% | All 8 buttons functional |
| Interrupts | 100% | VBlank, STAT, Timer, Serial, Joypad |
| Timer | 100% | DIV, TIMA, TMA, TAC with edge cases |
| Boot ROM | 100% | Full simulation of DMG boot sequence |
| Serial Link | 20% | Output only, no link cable |

### Not Implemented
- Audio (APU) - 0%
- Memory Bank Controller - 0%

### Test Results

#### Blargg Test ROMs
- cpu_instrs: 11/11 PASS
- instr_timing: 11/11 PASS
- mem_timing: Not tested
- Individual instruction tests: All passing

#### Game Compatibility
| Game | Boot | Graphics | Input | Status |
|------|------|----------|-------|--------|
| Tetris | Yes | Yes | Yes | Playable |
| Dr. Mario | Not tested | - | - | - |
| Super Mario Land | Not tested | - | - | - |

## Component Implementation Details

### Timer System

Implements all four timer registers with sophisticated features:

**DIV Register (0xFF04)**
- Increments every 256 T-cycles (64 M-cycles)
- Writing any value resets to 0
- Correctly calculated from system counter

**TIMA/TMA/TAC Registers**
- All 4 timer frequencies: 4096 Hz, 262144 Hz, 65536 Hz, 16384 Hz
- TIMA increments at exact intervals
- Timer enable/disable works
- TMA reload on overflow
- Timer interrupt triggered correctly

**Advanced Features**
- Falling-edge detection for TIMA increments
- TAC write obscure behavior (edge detection on writes)
- TIMA overflow delay (1 M-cycle before TMA reload)
- Writes to TIMA during overflow cancel reload

**Implementation**
Uses a 16-bit system counter that increments by 4 every M-cycle:
- DIV = system_counter / 256
- TIMA increments on falling edge of selected bit
  - Bit 9 for freq 0 (4096 Hz)
  - Bit 3 for freq 1 (262144 Hz)
  - Bit 5 for freq 2 (65536 Hz)
  - Bit 7 for freq 3 (16384 Hz)

### PPU Implementation

**Completed Features**

LCD Registers:
- LCDC (0xFF40): LCD control register
- STAT (0xFF41): Status register with mode flags
- SCX/SCY (0xFF42-43): Background scrolling
- LY (0xFF44): Current scanline counter
- LYC (0xFF45): LY compare for coincidence interrupt
- BGP (0xFF47): Background palette

PPU Modes & Timing:
- Mode 0: HBlank (204 T-cycles)
- Mode 1: VBlank (4560 T-cycles, 10 scanlines)
- Mode 2: OAM Search (80 T-cycles)
- Mode 3: Pixel Transfer (172 T-cycles)
- Accurate scanline timing (456 T-cycles per line)
- Frame timing (70224 T-cycles at 60 FPS)

Background Rendering:
- Tile-based rendering (8x8 pixel tiles)
- 256x256 pixel background (32x32 tiles)
- Scrolling support (SCX/SCY registers)
- Tile map reading (0x9800-0x9BFF or 0x9C00-0x9FFF)
- Tile data reading (0x8000-0x8FFF or 0x8800-0x97FF)
- Signed/unsigned tile addressing modes
- Palette support (4 colors, 2-bit per pixel)

Sprite Layer:
- 40 sprites in OAM
- 8x8 and 8x16 sprite modes
- X/Y flipping
- Priority system (above/behind background)
- Color 0 transparency
- Dual palettes (OBP0, OBP1)
- 10 sprites per scanline limit

Interrupts:
- VBlank interrupt (bit 0 of IF)
- STAT interrupts (HBlank, VBlank, LYC coincidence)
- Proper interrupt timing

**Tile Format**

Each tile is 8x8 pixels, stored as 16 bytes:
- 2 bytes per row (8 rows total)
- Each pixel uses 2 bits (one from each byte)
- Bit 7 = leftmost pixel, Bit 0 = rightmost

**Timing Accuracy**
- Scanline advances every 456 T-cycles
- VBlank occurs at line 144
- Mode transitions are accurate
- One frame = 70224 T-cycles

### Joypad Implementation

**Keyboard Mapping**

Buttons:
- A: A key
- B: S key
- Start: Z key
- Select: X key

D-Pad:
- Up: I key
- Down: K key
- Left: J key
- Right: L key

System:
- Quit: ESC key

**P1 Register (0xFF00)**

Bit Layout:
```
Bit 7-6: Not used (always 1)
Bit 5:   P15 Select Button Keys (0=Select)
Bit 4:   P14 Select Direction Keys (0=Select)
Bit 3:   P13 Input Down or Start (0=Pressed)
Bit 2:   P12 Input Up or Select (0=Pressed)
Bit 1:   P11 Input Left or B (0=Pressed)
Bit 0:   P10 Input Right or A (0=Pressed)
```

**Reading Buttons**
1. Game writes to P1 to select button group
2. Game reads P1 to get button states (bits 0-3)
3. 0 = pressed, 1 = not pressed (inverted logic)

**Interrupts**
- Joypad interrupt (bit 4 of IF register) triggered when any button is pressed
- Game can enable joypad interrupt via IE register (bit 4)
- Used to wake from HALT or handle input immediately

## Resolved Bugs

### LCDC/DMA Write Confusion (2026-01-11)
**Component:** Memory (I/O Registers)

**Problem:**
Game ROM contains a loop that writes 0x2F to 10 consecutive I/O registers including LY (read-only) and DMA.

**Solution:**
1. Made LY (0xFF44) read-only - writes now ignored
2. Added unused I/O register protection
3. Verified LCDC and DMA handlers properly separated

**Files Modified:** src/memory.py

### VRAM/OAM Access When LCD OFF (2026-01-10)
**Component:** Memory/PPU

**Problem:**
VRAM and OAM were blocked even when LCD was disabled. Games turn OFF LCD to safely write to VRAM.

**Solution:**
Added LCDC bit 7 check before applying restrictions.

**Files Modified:** src/memory.py

### LY Counter Stops When LCD OFF (2026-01-10)
**Component:** PPU

**Problem:**
LY register reset to 0 and stopped advancing when LCD turned off.

**Solution:**
LY continues to increment 0-153 even when LCD is disabled.

**Files Modified:** src/ppu.py

### Joypad Input Not Detected (2026-01-10)
**Component:** Joypad

**Problem:**
Button presses not detected. P1 register always returned 0xCF regardless of button state.

**Root Cause:**
1. Initial value was 0xC0 instead of 0xCF
2. Used |= operator to mark pressed buttons (can only SET bits, not clear them)

**Solution:**
Changed to use &= operator to clear bits for pressed buttons.

**Files Modified:** src/joypad.py

### Sprite Rendering Not Implemented (2026-01-09)
**Component:** PPU

**Solution:**
Implemented complete sprite rendering system with all features:
- OAM reading from 0xFE00-0xFE9F (40 sprites, 4 bytes each)
- 8x8 and 8x16 sprite modes
- Sprite priority (above/behind BG)
- Color 0 transparency
- X and Y flipping
- Dual sprite palettes OBP0/OBP1
- 10 sprites per scanline hardware limit
- Proper sprite ordering

**Files Modified:** src/ppu.py

### Boot ROM Simulation Missing (2026-01-09)
**Component:** Memory/CPU

**Problem:**
Emulator didn't simulate Game Boy boot sequence. VRAM contained garbage, hardware registers not initialized.

**Solution:**
Implemented complete boot ROM simulation:

Memory:
- Clears VRAM to 0x00
- Initializes all hardware registers
- Clears OAM to 0x00
- Disables boot ROM, maps cartridge to 0x0000-0x00FF

CPU:
- A=0x01, F=0xB0 (Z=1, N=0, H=1, C=1)
- BC=0x0013, DE=0x00D8, HL=0x014D
- SP=0xFFFE, PC=0x0100

**Files Modified:** src/memory.py, src/cpu.py

## Known Issues

### DMA Implementation Simplified
**Severity:** Low
**Component:** Memory

**Current Implementation:**
- Instant copy of 160 bytes from source to OAM
- Advances CPU cycle count by 640
- Does NOT properly stall CPU during DMA

**Real Hardware:**
- CPU can only access HRAM (0xFF80-0xFFFE) during DMA
- All other memory access returns 0xFF
- DMA takes 160 M-cycles with CPU stalled

**Impact:**
Most games work fine with instant DMA. Some games might have timing issues. Not yet observed to cause problems.

## Common Bug Patterns Observed

**Register Access Bugs:**
- Read-only registers accepting writes (LY)
- Missing register implementations
- Incorrect initial values

**Memory Access Bugs:**
- Not checking LCD enable before restricting access
- Incorrect PPU mode checks
- Missing special case handling

**Logic Bugs:**
- Using wrong operators (|= vs &=)
- Incorrect bit manipulation
- Off-by-one errors

## Lessons Learned

1. Always check LCD enable (LCDC bit 7) before applying PPU restrictions
2. Read-only registers must ignore writes
3. Boot ROM simulation critical for proper initialization
4. Bit manipulation requires careful operator selection
5. Test with actual games, not just test ROMs
