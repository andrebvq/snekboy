# Changelog

## 0.3.0 — Cartridge mappers

- MBC1, MBC2, MBC3 (with real-time clock) and MBC5, chosen from the ROM header.
- Battery saves: `<rom>.sav` (and `<rom>.rtc` for the clock), written on quit.
- STOP waits for a button press instead of acting on a Game Boy Color register.
- Fixed: signed tile numbers used the wrong base address (0x8800 instead of 0x9000),
  scrambling many games' graphics. Planned for 0.6, pulled forward.

Tests: Blargg 17/33 (combined cpu_instrs now passes), mooneye 53/111 (was 28),
MBC tests 27/28. All 12 test games reach their title or intro screen.

## 0.2.0 — Memory map

- Writes to ROM (0x0000-0x7FFF) are ignored. Fixes the Tetris crash when a game starts.
- Echo RAM writes now mirror to work RAM; 0xFEA0-0xFEFF is unusable.
- Unused I/O register bits read as 1; unmapped registers read 0xFF.
- Boot ROM switch (FF50) works.
- Illegal opcodes lock the CPU instead of crashing the emulator.
- After boot, P1 reads 0xCF and DIV counts on from 0xAB.

Tests: Blargg 16/33 non-sound ROMs pass (was 15), mooneye 28/111 (was 24).
