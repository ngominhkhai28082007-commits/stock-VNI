import os
print(f"CWD: {os.getcwd()}")
try:
    print(f"Listdir: {os.listdir('.')}")
except Exception as e:
    print(f"Listdir FAILED: {e}")

try:
    parent = os.path.dirname(os.getcwd())
    print(f"Parent: {parent}")
    print(f"Listdir Parent: {os.listdir(parent)}")
except Exception as e:
    print(f"Listdir Parent FAILED: {e}")
