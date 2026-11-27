# Changelog

## 0.2.0 — Memory map

- Writes to ROM (0x0000-0x7FFF) are ignored. Fixes the Tetris crash when a game starts.
- Echo RAM writes now mirror to work RAM; 0xFEA0-0xFEFF is unusable.
- Unused I/O register bits read as 1; unmapped registers read 0xFF.
- Boot ROM switch (FF50) works.
- Illegal opcodes lock the CPU instead of crashing the emulator.
- After boot, P1 reads 0xCF and DIV counts on from 0xAB.

Tests: Blargg 16/33 non-sound ROMs pass (was 15), mooneye 28/111 (was 24).
