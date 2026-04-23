import re

with open('server/quantamed/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<span>Gabi</span>', 'Gabi')

text = re.sub(r'\bGabi\b', '<span class="dyn-patient-name">Gabi</span>', text)
text = re.sub(r'\bGABI\b', '<span class="dyn-patient-name-upper">GABI</span>', text)

with open('server/quantamed/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replaced successfully")
