import re
import os

filepath = r"d:\fyeshi\project\quantum\shiva vro\drug-triage-env\server\quantamed\index.html"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace fonts
fonts_to_sans = ['DM Sans', 'Outfit', 'Rajdhani']
fonts_to_mono = ['DM Mono', 'Space Mono', 'JetBrains Mono']

for font in fonts_to_sans:
    content = re.sub(fr"font-family:\s*'{font}'[^;]*;", "font-family: 'IBM Plex Sans', sans-serif;", content)
    content = re.sub(fr"font-family:\s*\"{font}\"[^;]*;", "font-family: 'IBM Plex Sans', sans-serif;", content)

for font in fonts_to_mono:
    content = re.sub(fr"font-family:\s*'{font}'[^;]*;", "font-family: 'IBM Plex Mono', monospace;", content)
    content = re.sub(fr"font-family:\s*\"{font}\"[^;]*;", "font-family: 'IBM Plex Mono', monospace;", content)

# Remove excessive border-radius
content = re.sub(r"border-radius:\s*([2-9][0-9]|[1-9][0-9]{2,})px", "border-radius: 6px", content)
content = re.sub(r"border-radius:\s*[1-9]rem", "border-radius: 6px", content)
content = re.sub(r"border-radius:\s*50%;", "border-radius: 50%;", content) # keep circles

# Remove glassmorphism/blurs
content = re.sub(r"backdrop-filter:[^;]+;", "", content)
content = re.sub(r"-webkit-backdrop-filter:[^;]+;", "", content)

# Simplify shadows
content = re.sub(r"box-shadow:[^;]+;", "box-shadow: none;", content)
content = re.sub(r"text-shadow:[^;]+;", "text-shadow: none;", content)
content = re.sub(r"filter:\s*drop-shadow[^;]+;", "filter: none;", content)

# Remove background gradients and replace with flat colors where possible
content = re.sub(r"background:\s*linear-gradient\([^;]+;", "background: var(--bg-elevated);", content)
content = re.sub(r"background-image:\s*linear-gradient\([^;]+;", "background-image: none;", content)

# Remove glowing buttons logic
content = re.sub(r"border:\s*1px\s+solid\s+rgba\(0,\s*212,\s*255,\s*0\.[1-9]+\)", "border: 1px solid var(--border-default)", content)
content = re.sub(r"border:\s*1px\s+solid\s+rgba\(255,\s*82,\s*82,\s*0\.[1-9]+\)", "border: 1px solid var(--border-default)", content)
content = re.sub(r"border:\s*1px\s+solid\s+rgba\(0,\s*230,\s*118,\s*0\.[1-9]+\)", "border: 1px solid var(--border-default)", content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Mass replacement completed!")
