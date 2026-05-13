import os
path = r"C:\Users\Ngo Minh Khai\test_root.txt"
print(f"Trying to write to: {path}")
try:
    with open(path, "w") as f:
        f.write("test")
    print("Write SUCCESS")
    os.remove(path)
    print("Cleanup SUCCESS")
except Exception as e:
    print(f"Write FAILED: {e}")
