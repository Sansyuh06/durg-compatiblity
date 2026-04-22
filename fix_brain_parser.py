"""Fix the double-escaped OBJ parser in index.html."""
import re

with open('server/quantamed/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The file has literal \\n (two chars: backslash, n) where it should have \n (newline escape)
# And literal \\s where it should have \s (regex whitespace)
# In the JS source: text.split('\\n') should be text.split('\n')
# In the JS source: split(/\\s+/) should be split(/\s+/)

# Fix: replace the double-backslash versions with single-backslash
old_split = "text.split('\\\\n')"
new_split = "text.split('\\n')"
count1 = content.count(old_split)
content = content.replace(old_split, new_split)

old_regex = "split(/\\\\s+/)"
new_regex = "split(/\\s+/)"
count2 = content.count(old_regex)
content = content.replace(old_regex, new_regex)

with open('server/quantamed/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Replaced {count1} occurrences of split('\\\\n') -> split('\\n')")
print(f"Replaced {count2} occurrences of split(/\\\\s+/) -> split(/\\s+/)")

# Verify
with open('server/quantamed/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f"\nLine 2767: {repr(lines[2766])}")
print(f"Line 2768: {repr(lines[2767])}")
