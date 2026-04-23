import re

def main():
    with open('server/quantamed/index.html', 'r', encoding='utf-8') as f:
        text = f.read()

    # Replace UI text while keeping URLs intact
    text = text.replace('QuantaMed', 'Foldables')
    text = text.replace('QUANTAMED', 'FOLDABLES')
    text = text.replace('quantamed.com', 'foldables.com')

    # Revert API and directory paths
    text = text.replace('/api/Foldables/', '/api/quantamed/')
    text = text.replace('/api/FOLDABLES/', '/api/quantamed/')
    text = text.replace('/Foldables/static/', '/quantamed/static/')
    text = text.replace('id="Foldables', 'id="quantamed')
    text = text.replace('class="Foldables', 'class="quantamed')

    # Also, update the logo in the top bar
    old_logo = '<div class="nav-brand">FOLDABLES</div>'
    new_logo = '<div class="nav-brand" style="display:flex; align-items:center;"><img src="/quantamed/static/logo.png" style="height:24px; margin-right:8px; vertical-align:middle;" onerror="this.style.display=\'none\'">FOLDABLES</div>'
    text = text.replace(old_logo, new_logo)

    with open('server/quantamed/index.html', 'w', encoding='utf-8') as f:
        f.write(text)

    # Now update app.py and scoring_engine.py and pdf_report.py
    for fname in ['server/app.py', 'server/scoring_engine.py']:
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace('QuantaMed', 'Foldables')
            content = content.replace('QUANTAMED', 'FOLDABLES')
            content = content.replace('/api/Foldables/', '/api/quantamed/')
            content = content.replace('/Foldables/static/', '/quantamed/static/')
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(content)
        except FileNotFoundError:
            pass

if __name__ == '__main__':
    main()
