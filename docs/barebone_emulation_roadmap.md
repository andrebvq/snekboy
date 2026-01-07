# Barebone Game Boy Emulation - Critical Missing Pieces

## Current Status Assessment

### ✅ COMPLETE
1. **CPU Core** - All instructions implemented, tests 01-02 pass
2. **Memory System** - ROM/RAM, memory map, banking basics
3. **Timer System** - DIV, TIMA, TMA, TAC all working
4. **Interrupts** - Basic interrupt handling (IE, IF registers)
5. **Serial Output** - For test ROM communication

### ❌ MISSING - Critical for Barebone Emulation

## Priority 1: ABSOLUTE MINIMUM (Can run simple ROMs)

### 1. **LCD/PPU (Picture Processing Unit)** ⭐ HIGHEST PRIORITY
**Why Critical**: Without graphics, you can't see anything. Even basic ROMs need screen output.

**Minimum Implementation Needed**:
- **LCD Control Register (LCDC, 0xFF40)**: Enable/disable LCD, background, sprites
- **LCD Status Register (STAT, 0xFF41)**: Mode flags, coincidence flag
- **Scroll Registers (SCX, SCY, 0xFF42-43)**: Background scrolling
- **LY Register (0xFF44)**: Current scanline being drawn
- **Background Tile Map**: Read and render tiles from VRAM
- **Mode Timing**: 4 PPU modes (OAM search, pixel transfer, HBlank, VBlank)
- **VBlank Interrupt**: Signal when frame is ready

**Complexity**: Medium (2-3 days of work)
**Impact**: Makes emulator usable - you can actually SEE games run

**Files Needed**:
- `src/ppu.py` - PPU implementation
- Display window (SDL, pygame, or terminal-based)

---

### 2. **Joypad Input** ⭐ HIGH PRIORITY
**Why Critical**: Can't play games without input!

**Minimum Implementation Needed**:
- **Joypad Register (P1, 0xFF00)**: Read button states
- **Button/Direction Selection**: Matrix scanning (bit 4/5)
- **Joypad Interrupt**: Trigger on button press
- Keyboard mapping to Game Boy buttons (A, B, Start, Select, D-Pad)

**Complexity**: Low (few hours)
**Impact**: Enables interactive testing and actual gameplay

**Files Needed**:
- `src/joypad.py` - Joypad input handling
- Keyboard event handling in main loop

---

### 3. **Sound (Optional for Barebone)** ⏸️ LOW PRIORITY
**Why Can Skip Initially**: Games work without sound, just silent

**Needed Eventually**:
- 4 sound channels (2 square wave, 1 wave, 1 noise)
- Sound registers (NR10-NR52)
- Audio output buffer

**Complexity**: High (1 week+)
**Impact**: Nice to have but not critical for initial testing

---

## Priority 2: ENHANCED FUNCTIONALITY (Better compatibility)

### 4. **MBC (Memory Bank Controllers)**
**Current Status**: Basic ROM loading exists, but no banking
**Why Needed**: Most games >32KB need banking

**Common MBC Types** (in priority order):
- **MBC1**: Most common (70% of games)
- **MBC3**: Has RTC (Real-Time Clock)
- **MBC5**: Used by later games
- **No MBC**: Games <32KB (already works)

**Complexity**: Medium (1-2 days per MBC type)
**Impact**: Increases game compatibility from ~5% to ~90%

**Files Needed**:
- `src/mbc/mbc1.py`
- `src/mbc/mbc3.py`
- `src/mbc/mbc5.py`

---

### 5. **Save States / Battery RAM**
**Why Needed**: Games like Pokemon need to save progress

**Implementation**:
- Detect battery-backed RAM from ROM header
- Save/load .sav files
- Persist external RAM to disk

**Complexity**: Low (few hours)
**Impact**: Makes RPGs and long games playable

---

## Priority 3: NICE TO HAVE (Polish & accuracy)

### 6. **Sprite Rendering**
**Status**: Not implemented
**Why Needed**: Most games use sprites for characters/enemies

**Implementation**:
- OAM (Object Attribute Memory) at 0xFE00-FE9F
- Sprite tile fetching
- Sprite priority and transparency
- Sprite-background interaction

**Complexity**: Medium (2-3 days)
**Impact**: Essential for most games to look correct

---

### 7. **Window Layer**
**Status**: Not implemented
**Why Needed**: Some games use window for HUD/menus

**Implementation**:
- Window position registers (WX, WY)
- Window tile map
- Window enable bit in LCDC

**Complexity**: Low (few hours after background works)
**Impact**: Minor - only some games use it

---

### 8. **DMA Transfer**
**Status**: Unknown
**Why Needed**: Fast sprite data transfer

**Implementation**:
- DMA register (0xFF46)
- Copy 160 bytes from ROM/RAM to OAM
- Takes 160 M-cycles

**Complexity**: Low (1 hour)
**Impact**: Required for most games with sprites

---

## Minimum Viable Emulator Checklist

To run a simple game like **Tetris** or **Dr. Mario**:

- [x] CPU instructions
- [x] Memory system
- [x] Timer (basic)
- [x] Interrupts (basic)
- [ ] **LCD/PPU - Background rendering**
- [ ] **VBlank interrupt**
- [ ] **Joypad input**
- [ ] **Display window**

To run **Pokemon** or **Zelda**:
- All of the above, plus:
- [ ] **MBC1 or MBC3**
- [ ] **Sprite rendering**
- [ ] **Save/load functionality**
- [ ] **More accurate timing**

---

## Recommended Implementation Order

### Phase 1: Visual Output (Week 1)
1. ✅ Basic PPU - Background tiles only
2. ✅ Scanline rendering
3. ✅ VBlank interrupt
4. ✅ Display window (SDL/pygame)
5. ✅ Test with boot ROM or simple test

**Deliverable**: Can see graphics on screen

---

### Phase 2: Interactivity (Week 1-2)
1. ✅ Joypad input
2. ✅ Test with Tetris or Dr. Mario
3. ✅ Fix any graphical glitches

**Deliverable**: Can play simple games

---

### Phase 3: Game Compatibility (Week 2-3)
1. ✅ MBC1 implementation
2. ✅ Sprite rendering
3. ✅ DMA transfer
4. ✅ Battery RAM / save states
5. ✅ Test with Pokemon, Zelda, etc.

**Deliverable**: Can play major commercial games

---

### Phase 4: Polish (Week 4+)
1. ✅ Sound (if desired)
2. ✅ Window layer
3. ✅ More accurate timing
4. ✅ Debug tools (memory viewer, debugger)
5. ✅ UI improvements

**Deliverable**: Full-featured emulator

---

## Immediate Next Step Recommendation

**START WITH LCD/PPU BACKGROUND RENDERING**

This is the #1 priority because:
1. Makes the emulator actually usable
2. Enables visual testing
3. Required for literally every game
4. Not overly complex to get basic version working
5. Very satisfying to see graphics appear!

### Suggested Approach:

1. **Minimal PPU** (Day 1):
   - Implement scanline counter (LY)
   - Basic mode timing (VBlank, HBlank)
   - Read background tile data from VRAM
   - Render to a simple buffer

2. **Display Output** (Day 1-2):
   - Create 160x144 window
   - Convert tile data to pixels
   - Display each frame
   - Lock to 60 FPS

3. **Test & Iterate** (Day 2-3):
   - Load simple test ROMs
   - Fix rendering bugs
   - Add scroll support
   - Verify VBlank timing

4. **Add Joypad** (Day 3):
   - Map keyboard to buttons
   - Implement P1 register
   - Test interactivity

After this, you'll have a **functional, playable emulator** even if it only supports simple games!

---

## Resource Estimates

**Time to Barebone Emulator** (can play Tetris):
- With focused work: **3-5 days**
- Casual pace: **1-2 weeks**

**Time to Commercial Game Support** (Pokemon, Zelda):
- With focused work: **2-3 weeks**
- Casual pace: **1-2 months**

**Current Progress**: ~60% (CPU, Memory, Timer done - the hard parts!)

---

## Quick Start: Next Command

Want to get started immediately? I can:
1. Implement basic PPU with background rendering
2. Add a simple display window (pygame/SDL)
3. Test with a boot ROM or Tetris

This would give you **visual output** in a few hours of work!
