"""Memory-map behaviour checked against DMG hardware (Pan Docs, "Memory Map")."""

from src.cpu import CPU


def _cpu_with_rom(size=0x8000, fill=0x00):
    cpu = CPU()
    cpu.memory.load_rom(bytes([fill]) * size)
    cpu.simulate_boot()
    return cpu


def test_rom_writes_are_ignored():
    cpu = _cpu_with_rom(fill=0x20)
    mem = cpu.memory
    # Tetris writes 0x01 to 0x2000 (an MBC bank-select write); ROM must not change.
    mem.write_byte(0x2000, 0x01)
    mem.write_byte(0x0000, 0xFF)
    mem.write_byte(0x7FFF, 0xFF)
    assert mem.read_byte(0x2000) == 0x20
    assert mem.read_byte(0x0000) == 0x20
    assert mem.read_byte(0x7FFF) == 0x20


def test_echo_ram_writes_reach_wram():
    cpu = _cpu_with_rom()
    mem = cpu.memory
    mem.write_byte(0xFDFF, 0x80)          # echo of 0xDDFF
    assert mem.read_byte(0xDDFF) == 0x80
    mem.write_byte(0xC123, 0x42)
    assert mem.read_byte(0xE123) == 0x42


def test_unusable_area_reads_zero_and_ignores_writes():
    cpu = _cpu_with_rom()
    mem = cpu.memory
    cpu.memory._data[0xFF40] = 0x00       # LCD off, so OAM is never locked
    mem.write_byte(0xFEF9, 0xFC)
    assert mem.read_byte(0xFEF9) == 0x00
    assert mem.read_byte(0xFEA0) == 0x00
