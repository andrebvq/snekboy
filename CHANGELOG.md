# Changelog

All notable changes to SnekBoy, newest first. Each release is one merged pull
request with a matching git tag. The [Developer's Logbook](docs/developer_logbook.html)
explains every release in depth: what was wrong, how it was found, and why each
fix is correct.

Test counts: Blargg = 33 non-sound ROMs, mooneye = 111 ROMs, unit tests = pytest.
Speed is uncapped frames per second on Python 3.10; 60 is full speed.

## 0.9.2 — Frame loop

Removes most of the per-instruction call overhead.

- Each frame runs in one inline loop for the common case (CPU running,
  code in ROM/RAM, no DMA or pending interrupt); anything else goes
  through step() as before.

No change in behaviour: every executed instruction of 12 games matches
v0.9.1; test results unchanged. Gameplay speed of the slower games up
6-33% (Kirby 39 -> 51 fps, Tetris 41 -> 51, Zelda DX 53 -> 66).

## 0.9.1 — Lazy timer/PPU sync

Stops updating the timer and PPU after instructions nothing could observe.

- In the frame loop the timer and PPU are brought up to date only when
  something could observe them (I/O or video memory access, a possible
  interrupt, end of frame) instead of after every instruction.

No change in behaviour: every executed instruction of 12 games matches
v0.9; test results unchanged. Busy-waiting games 12-22% faster (Tetris
36 -> 44 fps, Kirby 33 -> 40, Zelda DX 34 -> 41).

## 0.9.0 — Speed, part 2

Faster instructions and an idle CPU that skips ahead.

- Dedicated handlers for the frequent instructions (loads, arithmetic,
  jumps, calls, LDH, all CB ops), generated from templates.
- A halted CPU skips ahead to the next PPU or timer event instead of
  idling one cycle at a time.
- The frame loop keeps fixed frame ends (emulated time ran ~0.02% slow).
- Window title shows the version; P switches between an
  evenly spaced green palette (new default), the classic one and grey.

No change in behaviour: every executed instruction of 12 games matches
v0.8 cycle for cycle; test results unchanged. 6 of 11 tested games now
reach full speed (e.g. Super Mario Land 36 -> 116 fps uncapped; the window
is capped at 60); Tetris 29 -> 36 fps.

## 0.8.0 — CPU speed

A three-fold speed-up of the CPU with identical behaviour.

- Opcodes are decoded once at start-up into a dispatch table, replacing
  two long comparison chains per instruction.
- The timer counts TIMA ticks arithmetically between events instead of
  looping over every M-cycle.
- Flags are a plain byte; plain memory reads and register access skip
  helper layers.
- Removed the unused second decoder and executor.

No change in behaviour: CPU state and screens of 12 games match v0.7
frame for frame, test results unchanged. Tetris 8.8 -> 28 fps, Super
Mario Land 15 -> 36 fps (full speed is 60).

## 0.7.0 — Timing

Timing to the individual memory access.

- Each CPU memory access happens on its own cycle; the timer, PPU and
  OAM DMA catch up before any access that can see them.
- OAM DMA takes 160 cycles, blocks OAM, can be restarted, and reads
  sources 0xE0-0xFF from work RAM.
- Pixel transfer gets longer with fine scroll, the window and sprites;
  LY and the OAM/VRAM access locks change on their hardware dots.
- Serial transfers take 8 bits at 8192 Hz and raise the serial interrupt.
- Joypad interrupt only for buttons in the selected group.

Blargg 17 -> 26 passing (all of mem_timing), mooneye 66 -> 93. The tests
still failing are for other models (DMG0, MGB, SGB, CGB), MBC1 multicart
and the DMG OAM corruption bug. About 5% slower.

## 0.6.0 — Graphics (PPU)

Correct window, sprite priority, LCD on/off and STAT interrupts.

- Window keeps its own line counter, is hidden when the background is off,
  and shifts left for WX < 7.
- Sprite-behind-background checks the background colour number, not the
  shade; overlapping sprites resolve by X then OAM index.
- LCD off stops the PPU (LY 0, no interrupts, blank screen); LCD on
  restarts at line 0.
- STAT interrupt fires once per rising edge of the combined STAT line;
  STAT writes keep read-only bits; LYC writes re-check the match.
- Line 153 reads LY 0 after its first dots.

dmg-acid2 now matches the reference (818 wrong pixels -> 0).
mooneye 62 -> 66 passing; Blargg unchanged. Wario Land II no longer stops
at a white screen after its intro.

## 0.5.0 — Interrupts and timer

Interrupt and timer edge cases as tested by mooneye.

- `DI` right after `EI` no longer lets an interrupt through.
- A second `EI` no longer restarts the one-instruction delay.
- Interrupt dispatch is decided after pushing PC's high byte; a push that
  overwrites IE can cancel it, as on hardware.
- `EI; HALT` with an interrupt waiting returns to the `HALT` instead of
  corrupting the handler's first instruction.
- Writing DIV can tick TIMA (falling edge of the selected counter bit).
- During the cycle TIMA reloads from TMA, TIMA writes are ignored and TMA
  writes also reach TIMA.
- Removed unused `src/timer.py`.

mooneye 53 -> 62 passing. Blargg and game output unchanged.

## 0.4.0 — Speed

First performance pass.

- Graphics decode each 8-pixel tile row with one table lookup and read video memory directly.
- Fast path for ROM and RAM reads; Gameboy Doctor mode checked once at start.
- The frame is drawn to the window in one call instead of pixel by pixel.
- Fixed: Gameboy Doctor mode no longer freezes the graphics.

About 2-3x faster (Tetris 4.5 -> 9.6 fps, Super Mario Land 5.2 -> 15.9 fps).
Output and test results are unchanged.

## 0.3.0 — Cartridge mappers

Games larger than 32 KB.

- MBC1, MBC2, MBC3 (with real-time clock) and MBC5, chosen from the ROM header.
- Battery saves: `<rom>.sav` (and `<rom>.rtc` for the clock), written on quit.
- STOP waits for a button press instead of acting on a Game Boy Color register.
- Fixed: signed tile numbers used the wrong base address (0x8800 instead of 0x9000),
  scrambling many games' graphics. Pulled forward from the graphics release.

Tests: Blargg 17/33 (combined cpu_instrs now passes), mooneye 53/111 (was 28),
MBC tests 27/28. All 12 test games reach their title or intro screen.

## 0.2.0 — Memory map

Memory and I/O behave as on DMG hardware; fixes the Tetris crash.

- Writes to ROM (0x0000-0x7FFF) are ignored. Fixes the Tetris crash when a game starts.
- Echo RAM writes now mirror to work RAM; 0xFEA0-0xFEFF is unusable.
- Unused I/O register bits read as 1; unmapped registers read 0xFF.
- Boot ROM switch (FF50) works.
- Illegal opcodes lock the CPU instead of crashing the emulator.
- After boot, P1 reads 0xCF and DIV counts on from 0xAB.

Tests: Blargg 16/33 non-sound ROMs pass (was 15), mooneye 28/111 (was 24).

## 0.1.0 — First working version

The starting point, before the audit that drove 0.2 onwards.

- All 245 defined opcodes and 256 CB opcodes, with flags and instruction
  timing; background, window and sprite rendering; timer, interrupts,
  joypad, simulated boot state; pygame display; trace file and Gameboy
  Doctor log.
- ROM-only cartridges up to 32 KB; no mappers.

Tests: Blargg 15/33 (the 11 `cpu_instrs` singles and `instr_timing` pass),
mooneye 24/111, unit tests 12/13. Tetris crashes when a game starts.
About a tenth of full speed.
