import os
import subprocess

def get_short_path(path):
    import ctypes
    from ctypes import wintypes
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    
    output_buf_size = 256
    output_buf = ctypes.create_unicode_buffer(output_buf_size)
    _GetShortPathNameW(path, output_buf, output_buf_size)
    return output_buf.value

cwd = os.getcwd()
print(f"CWD: {cwd}")
try:
    short_path = get_short_path(cwd)
    print(f"Short Path: {short_path}")
    test_path = os.path.join(short_path, "test_short.txt")
    print(f"Trying to write to: {test_path}")
    with open(test_path, "w") as f:
        f.write("test")
    print("Write SUCCESS")
except Exception as e:
    print(f"Write FAILED: {e}")
