# Architecture

How SnekBoy is built, component by component. For the history behind each design choice, see the [Developer's Logbook](developer_logbook.html).

## Overview

| Component | File | Role |
|---|---|---|
| Emulator | `src/emulator.py` | Loads the ROM and save, runs one frame per loop iteration, renders, paces to 60 fps, writes saves on quit |
| CPU | `src/cpu.py` | Fetch, decode and execute; interrupts; HALT/STOP; the timer; per-access timing; the frame loop |
| Decoder and handlers | `src/cpu_decoder.py`, `src/instructions_impl.py`, `src/fast_ops.py` | Decoding (used once, to build tables) and instruction semantics |
| Memory | `src/memory.py` | Address decoding, I/O registers, OAM DMA, serial port, PPU access locks, boot state |
| Cartridge | `src/cartridge.py` | Header parsing and the MBC1, MBC2, MBC3 (with clock) and MBC5 mappers |
| PPU | `src/ppu.py` | LCD modes and timing, the STAT interrupt line, line rendering |
| Joypad | `src/joypad.py` | The P1 register and the joypad interrupt |
| Display | `src/display.py` | pygame window, keyboard, palettes |

All emulated state lives in one 64 KB `bytearray` (`Memory._data`) plus the component objects. Regions without side effects (ROM, work RAM, high RAM) are read straight from that array, and everything else goes through `Memory.read_byte` / `write_byte`.

## Time

Time is counted in T-cycles: 4.194304 MHz, 4 per M-cycle and 70,224 per frame. `cpu.total_cycles` is the master clock.

### Per-access timing

On hardware, each memory access of an instruction happens on its own M-cycle, and the timer, PPU and DMA move on between them. SnekBoy models this with two counters per instruction:

- `_acc`: the T-cycles of the current instruction started so far. Each fetch, read, write and internal delay adds 4.
- `_synced`: how far the timer, PPU and DMA have been advanced within the instruction.

Before an access that could observe them (I/O at 0xFF00-0xFF7F, VRAM, OAM, or anything while OAM DMA runs), `_catch_up()` advances the other components by `_acc - _synced`. The rest is advanced when the instruction ends. A read of DIV, LY or STAT therefore sees the value of the exact cycle on which it happens.

### Lazy synchronisation (frame loop only)

Inside `run_until_cycle()`, advancing the timer and PPU after every instruction is unnecessary when nothing can observe them. The CPU instead owes the cycles (`_lag`) until one of these happens:

- an access that catches up (see above). It pays the owed cycles first, because they are folded into `_synced` at the start of each instruction;
- the owed cycles would reach `_budget`: the distance to the next point where the PPU or timer could raise an interrupt (`PPU.dots_to_next_event()`, TIMA overflow). Landing exactly on such a point syncs, so the interrupt check sees it;
- a halted, stopped or locked stretch, STOP, an illegal opcode, or the end of the run.

A write to 0xFF00-0xFF7F resets the budget, because TAC, LCDC, LYC, STAT and DIV can move the next event. During OAM DMA, a serial transfer, or a TIMA overflow or reload, the budget is 0, which means a sync after every instruction.

### HALT skip-ahead

A halted CPU advances straight to the earliest of: the caller's deadline, the next PPU event, or the TIMA overflow edge (`CPU._halt_skip`). It uses single M-cycles while DMA, serial or a TIMA reload is active. The timer and PPU change state only at fixed points and read nothing a halted CPU can change, so advancing them in one batch gives the same result as many small steps.

## CPU

### Dispatch

At start-up, `_build_dispatch()` runs every opcode once through the decoder with probe fetch functions. These record whether an operand byte or word is fetched and where it lands (the target or immediate slot). The result is a 256-entry table of `(handler, target, immediate, operand kind, slot, cycles)` and a 256-entry CB table. Fetch order and cycle counts come from the original decoder by construction.

`src/fast_ops.py` then replaces 439 entries with dedicated handlers generated from templates: LD r,r'/r,n, the 8-bit ALU on registers and immediates, INC/DEC r, JR/JP/CALL/RET with and without conditions, LDH, and all CB operations. Each handler has its register or condition written into its code and computes the flag byte in one expression. A differential test runs every dedicated handler against the generic one on random states.

### Frame loop

`run_until_cycle(target)` runs `_frame_loop`, which hoists the tables, the memory array and the registers into locals and executes the common case inline:

1. The interrupt check (IE & IF, only when IME is set).
2. The opcode, read straight from ROM, WRAM or HRAM.
3. Operand bytes, read straight when they are in those regions too, with the same `_acc` positions as the bus.
4. The handler call, the EI countdown and the lazy-sync accounting.

Anything else uses `step()` for that one instruction: halted, stopped, locked, HALT bug pending, OAM DMA running, PC elsewhere, an interrupt to dispatch, or an illegal opcode. `_on_instruction` is an optional hook called before each instruction, for tracing tools. With the Gameboy Doctor logger active, the loop uses `step()` throughout.

### Interrupts, HALT, STOP

- EI takes effect after the next instruction. DI cancels a pending EI.
- Dispatch takes 5 M-cycles. The interrupt is chosen after the high byte of PC is pushed, so a push that overwrites IE can cancel it (PC becomes 0x0000).
- HALT with IME clear and an interrupt pending triggers the HALT bug: the next byte is read twice. `EI; HALT` with an interrupt pending returns to the HALT.
- STOP resets DIV and freezes the CPU and timer until a selected joypad line goes low.
- The 11 undefined opcodes lock the CPU for good while the timer and PPU keep running.

### Timer

The timer is driven by a 16-bit system counter, of which DIV is the upper byte. TIMA counts falling edges of counter bit 9, 3, 5 or 7 (TAC 0-3) ANDed with the enable bit. That makes writes to DIV or TAC able to tick TIMA. On overflow, TIMA reads 0 for one M-cycle, then reloads from TMA and requests the interrupt. During that reload cycle, TIMA writes are ignored and TMA writes go through to TIMA.

Between events the edges are counted arithmetically, with `(new >> s) - (old >> s)` for s = 10, 4, 6 or 8. The exact per-M-cycle path is used around overflows, reloads and serial transfers. A unit test compares the two paths on random states.

## Memory

| Range | Behaviour |
|---|---|
| 0x0000-0x7FFF | ROM. Writes go to the mapper; ROM-only carts ignore them |
| 0x8000-0x9FFF | VRAM, locked to the CPU during mode 3 |
| 0xA000-0xBFFF | Cartridge RAM or MBC3 clock registers, when enabled |
| 0xC000-0xDFFF | Work RAM |
| 0xE000-0xFDFF | Echo of 0xC000-0xDDFF (reads and writes) |
| 0xFE00-0xFE9F | OAM, locked during modes 2 and 3 and during DMA |
| 0xFEA0-0xFEFF | Unusable: reads 0x00 (0xFF while OAM is locked), writes ignored |
| 0xFF00-0xFF7F | I/O. Unused bits read 1; unmapped registers read 0xFF |
| 0xFF80-0xFFFE | High RAM, the only RAM the CPU can use during OAM DMA |
| 0xFFFF | IE |

- **OAM DMA:** one setup M-cycle, then 160 M-cycles copying one byte each. OAM reads 0xFF while it runs, a new write to 0xFF46 restarts it, and sources 0xE0-0xFF read work RAM.
- **Serial:** with the internal clock, a transfer shifts one bit per falling edge of system-counter bit 8 (8192 Hz), then raises the serial interrupt. With no link partner, ones shift in.
- **Mappers:** a bank switch copies the selected 16 KB ROM bank into the array, so ROM reads stay a plain index. The MBC3 clock reads host time (injectable for tests). Battery RAM is saved as `<rom>.sav`, the clock as `<rom>.rtc`.

## PPU

A line is 456 dots: OAM search (80), pixel transfer (172 plus penalties), HBlank, and lines 144-153 as VBlank. The pixel-transfer length adds fine X scroll (SCX & 7), 6 dots when the window starts, and the sprite stalls, so HBlank and the STAT mode change happen on the right dot.

- **Rendering is line-based:** the whole line is drawn when pixel transfer starts, from the register values at that moment. Mid-line register changes are not shown (no game tested relies on them). Each 8-pixel tile row is decoded with one table lookup.
- **Window:** it has its own line counter, which advances only on lines where the window was drawn. It is hidden when LCDC bit 0 is off and shifts left for WX < 7.
- **Sprites:** up to 10 per line, chosen in OAM order. Where sprites overlap, lower X and then lower OAM index wins. The behind-background test uses the background colour number, not the shade.
- **STAT:** the four sources are ORed into one line, and the interrupt fires on its rising edge only. LY shows the next line 4 dots early, and line 153 reads LY 0 after its first dots.
- **LCD off** stops the PPU (LY 0, mode 0, a blank screen). LCD on restarts at line 0, without an OAM search on the first line.

## Verification method

Every release since 0.4 was checked against the previous one with harnesses kept outside the repository:

| Check | Compares |
|---|---|
| State fingerprints | CPU registers, cycle count and screen hash of 12 games every 30 frames |
| Screens with input | 20 screenshots per game over 1200 frames with scripted button presses |
| Instruction trace | A rolling SHA-1 over every executed instruction's cycle count and registers (from 0.9) |
| Test ROMs | Blargg and mooneye results against the previous release |
| dmg-acid2 | Pixel difference against the reference image |

Host inputs are pinned: buttons are scripted, and the MBC3 clock is frozen. Optimisations had to be identical on all of these. Behaviour changes were expected to move only the targeted tests.

## Known limitations

| Limitation | Effect |
|---|---|
| No APU | No sound; sound registers only store values, with unused bits reading 1 |
| No OAM corruption bug | 6 of Blargg's `oam_bug` ROMs fail; games are not known to depend on it |
| Line-based rendering | Mid-line raster effects are not shown |
| No MBC1 multicart | Compilation cartridges with the multicart wiring do not run |
| DMG only | No Game Boy Color mode; dual-mode games run in DMG mode |
| Speed | 6 of the 11 tested games run below 60 fps in gameplay on Python 3.10 |
