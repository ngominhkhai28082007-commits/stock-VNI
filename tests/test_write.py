import os
import sys

print(f"Current Working Directory: {os.getcwd()}")
try:
    with open("test_file.txt", "w") as f:
        f.write("test")
    print("Write to '.' SUCCESS")
except Exception as e:
    print(f"Write to '.' FAILED: {e}")

try:
    full_path = os.path.abspath("test_file_abs.txt")
    print(f"Trying absolute path: {full_path}")
    with open(full_path, "w") as f:
        f.write("test")
    print("Write to absolute path SUCCESS")
except Exception as e:
    print(f"Write to absolute path FAILED: {e}")
