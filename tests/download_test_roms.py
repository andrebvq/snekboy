"""
Download Blargg's Game Boy test ROMs

These ROMs are used to verify emulator accuracy.
They output "Passed" or "Failed: <reason>" to the serial port.
"""

import urllib.request
import os

TEST_ROMS = {
    'cpu_instrs': 'https://github.com/retrio/gb-test-roms/raw/master/cpu_instrs/cpu_instrs.gb',
    'instr_timing': 'https://github.com/retrio/gb-test-roms/raw/master/instr_timing/instr_timing.gb',
    'mem_timing': 'https://github.com/retrio/gb-test-roms/raw/master/mem_timing/mem_timing.gb',
}

def download_test_roms(output_dir='test_roms'):
    """Download test ROMs to specified directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    for name, url in TEST_ROMS.items():
        output_path = os.path.join(output_dir, f'{name}.gb')
        
        if os.path.exists(output_path):
            print(f'✓ {name}.gb already exists')
            continue
        
        print(f'Downloading {name}.gb...')
        try:
            urllib.request.urlretrieve(url, output_path)
            print(f'  → Saved to {output_path}')
        except Exception as e:
            print(f'  ✗ Failed: {e}')
    
    print(f'\nTest ROMs downloaded to {output_dir}/')

if __name__ == '__main__':
    download_test_roms()
