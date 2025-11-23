import os
import shutil
import datetime
import time
from src.organizer import PhotoOrganizer

def create_dummy_file(path, timestamp):
    with open(path, 'w') as f:
        f.write("dummy")
    os.utime(path, (timestamp, timestamp))

def test_organizer():
    base_dir = "test_env"
    src_dir = os.path.join(base_dir, "src")
    dest_dir = os.path.join(base_dir, "dest")
    
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(src_dir)
    
    # Create files with specific dates
    # File 1: 2023-01-01 10:00:00
    ts1 = datetime.datetime(2023, 1, 1, 10, 0, 0).timestamp()
    create_dummy_file(os.path.join(src_dir, "photo1.jpg"), ts1)
    
    # File 2: 2023-01-01 11:00:00 (Same day, later)
    ts2 = datetime.datetime(2023, 1, 1, 11, 0, 0).timestamp()
    create_dummy_file(os.path.join(src_dir, "photo2.jpg"), ts2)
    
    # File 3: 2023-01-02 09:00:00 (Different day)
    ts3 = datetime.datetime(2023, 1, 2, 9, 0, 0).timestamp()
    create_dummy_file(os.path.join(src_dir, "photo3.png"), ts3)

    organizer = PhotoOrganizer()
    files = organizer.scan_files(src_dir)
    print(f"Found {len(files)} files")
    
    # Test 1: Standard format
    print("\nTest 1: Standard format (%Y/%m/%d, IMG_{seq:04d})")
    ops = organizer.generate_operations(files, dest_dir, "%Y/%m/%d", "IMG_{seq:04d}")
    
    for op in ops:
        print(f"{os.path.basename(op['source'])} -> {op['dest']}")
        
    # Verify expectations
    # photo1 -> 2023/01/01/IMG_0001.jpg
    # photo2 -> 2023/01/01/IMG_0002.jpg
    # photo3 -> 2023/01/02/IMG_0001.png
    
    dest_paths = [os.path.normpath(op['dest']) for op in ops]
    
    # Helper to create normalized path suffix
    def norm(p):
        return os.path.normpath(p)

    assert any(norm("2023/01/01/IMG_0001.jpg") in p for p in dest_paths)
    assert any(norm("2023/01/01/IMG_0002.jpg") in p for p in dest_paths)
    assert any(norm("2023/01/02/IMG_0001.png") in p for p in dest_paths)
    print("Test 1 Passed!")

    # Test 2: Custom format
    print("\nTest 2: Custom format (%Y-%m-%d, Photo_{seq})")
    ops = organizer.generate_operations(files, dest_dir, "%Y-%m-%d", "Photo_{seq}")
    
    for op in ops:
        print(f"{os.path.basename(op['source'])} -> {op['dest']}")
        
    dest_paths = [os.path.normpath(op['dest']) for op in ops]
    assert any(norm("2023-01-01/Photo_1.jpg") in p for p in dest_paths)
    assert any(norm("2023-01-01/Photo_2.jpg") in p for p in dest_paths)
    print("Test 2 Passed!")

if __name__ == "__main__":
    test_organizer()
