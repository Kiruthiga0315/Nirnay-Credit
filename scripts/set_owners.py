"""Usage: python scripts/set_owners.py M1=@alice M2=@bob M3=@carol M4=@dave"""
import pathlib
import sys

path = pathlib.Path(__file__).resolve().parents[1] / ".github" / "CODEOWNERS"
text = path.read_text()
for arg in sys.argv[1:]:
    key, handle = arg.split("=", 1)
    text = text.replace(f"@{key.upper()}_HANDLE", handle)
path.write_text(text)
print("CODEOWNERS updated")
