import os
import tempfile
temp_dir = tempfile.gettempdir()
path = os.path.join(temp_dir, "test_temp.txt")
print(f"Trying to write to: {path}")
try:
    with open(path, "w") as f:
        f.write("test")
    print("Write SUCCESS")
    os.remove(path)
    print("Cleanup SUCCESS")
except Exception as e:
    print(f"Write FAILED: {e}")
