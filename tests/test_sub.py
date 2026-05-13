import os
path = "data/test.txt"
print(f"Trying to write to: {path}")
try:
    with open(path, "w") as f:
        f.write("test")
    print("Write SUCCESS")
except Exception as e:
    print(f"Write FAILED: {e}")
