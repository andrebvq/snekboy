from src.memory import Memory

def test_memory_read_write():
    mem = Memory()
    
    # Test byte operations
    mem.write_byte(0x1234, 0xAB)
    assert mem.read_byte(0x1234) == 0xAB
    
    # Test word operations (little-endian)
    mem.write_word(0x5000, 0x1234)
    assert mem.read_byte(0x5000) == 0x34  # Low byte
    assert mem.read_byte(0x5001) == 0x12  # High byte
    assert mem.read_word(0x5000) == 0x1234
    
    print("✓ Memory read/write test passed")

def test_echo_ram():
    mem = Memory()
    
    # Write to WRAM
    mem.write_byte(0xC000, 0x42)
    
    # Read from Echo RAM (should mirror)
    assert mem.read_byte(0xE000) == 0x42
    
    # Write to Echo RAM
    mem.write_byte(0xE100, 0x99)
    
    # Read from WRAM (should mirror)
    assert mem.read_byte(0xC100) == 0x99
    
    print("✓ Echo RAM mirror test passed")

def test_load_rom():
    mem = Memory()
    
    # Create fake ROM data
    rom_data = bytes([0x00, 0xC3, 0x50, 0x01])  # NOP, JP 0x0150
    mem.load_rom(rom_data)
    
    assert mem.read_byte(0x0000) == 0x00
    assert mem.read_byte(0x0001) == 0xC3
    assert mem.read_byte(0x0002) == 0x50
    assert mem.read_byte(0x0003) == 0x01
    
    print("✓ ROM loading test passed")

def test_memory_dump():
    mem = Memory()
    
    # Write some test data
    for i in range(16):
        mem.write_byte(0x0100 + i, i * 17)  # 0x00, 0x11, 0x22, etc.
    
    print("\n--- Memory Dump Test ---")
    mem.dump_region(0x0100, 0x010F)
    
    stats = mem.get_stats()
    print(f"\nMemory stats: {stats}")

if __name__ == "__main__":
    test_memory_read_write()
    test_echo_ram()
    test_load_rom()
    test_memory_dump()
    print("\n✓ All memory tests passed!")
