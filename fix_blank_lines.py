import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove excess blank lines (more than 2 consecutive newlines)
content = re.sub(r'\n\n\n+', '\n\n', content)

# Remove trailing whitespace at end of file
content = content.rstrip() + '\n'

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed blank lines and end-of-file")
