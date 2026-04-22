"""Verify the fix was applied correctly."""
with open('server/quantamed/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

line = lines[2766]
chars_around_split = line[line.index("split"):line.index("split")+25]
print(f"Raw chars: {repr(chars_around_split)}")
print(f"Hex: {[hex(ord(c)) for c in chars_around_split]}")

# Check if \\n (double backslash) still exists
if '\\\\n' in line:
    print("STILL DOUBLE-ESCAPED - fix not applied!")
elif '\\n' in line:
    print("CORRECT - single backslash-n (JS newline escape)")
