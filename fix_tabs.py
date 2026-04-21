import re

def main():
    filepath = r"server\quantamed\index.html"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Remove STEP 08 button
    content = re.sub(
        r'<button class="step-btn" onclick="showPanel\(6\.5, this\)"><span class="step-num">STEP 08</span>PROTEIN FOLDING</button>\n?',
        '',
        content
    )
    
    # 2. Extract panel6_5
    # Find the start of panel6_5
    start_match = re.search(r'<!-- ═+ -->\s*<!-- PANEL 6\.5: PROTEIN STRUCTURE SIMULATION.*?<!-- ═+ -->\s*<div class="panel" id="panel6_5">', content, re.DOTALL)
    if not start_match:
        print("Could not find start of panel6_5")
        return
        
    start_idx = start_match.start()
    
    # Find the start of panel7
    end_match = re.search(r'<!-- ═+ -->\s*<!-- PANEL 7: FINAL RECOMMENDATION.*?<!-- ═+ -->\s*<div class="panel" id="panel7">', content, re.DOTALL)
    if not end_match:
        print("Could not find end of panel6_5 (start of panel7)")
        return
        
    end_idx = end_match.start()
    
    panel_content = content[start_idx:end_idx]
    
    # Remove panel_content from its original location
    content = content[:start_idx] + content[end_idx:]
    
    # 3. Create view-protein wrapper and append before closing </div><!-- /app -->
    view_protein = f'\n  <div id="view-protein" class="mode-view">\n    <div style="padding: 24px; max-width: 1200px; margin: 0 auto;">\n{panel_content}    </div>\n  </div>\n'
    # We also need to change `class="panel"` to `class="panel active"` so it displays properly inside `view-protein`
    view_protein = view_protein.replace('id="panel6_5"', 'id="panel6_5" class="panel active"')
    
    content = content.replace('</div><!-- /app -->', f'</div>\n{view_protein}\n</div><!-- /app -->')
    
    # 4. Update switchMode
    old_switch_mode = """  } else if (mode === 'protein') {
    document.getElementById('view-quantamed').style.display = 'block';
    const triageView = document.getElementById('view-triage');
    if (triageView) triageView.style.display = 'none';
    // Jump to the protein simulation step (panel6_5)
    const btn = document.querySelectorAll('.step-btn')[7];
    showPanel(6.5, btn);
  }"""
    
    new_switch_mode = """  } else if (mode === 'protein') {
    document.getElementById('view-quantamed').style.display = 'none';
    const triageView = document.getElementById('view-triage');
    if (triageView) triageView.style.display = 'none';
    let proteinView = document.getElementById('view-protein');
    if (proteinView) proteinView.style.display = 'block';
  }"""
    content = content.replace(old_switch_mode, new_switch_mode)
    
    # 5. Fix autoAdvance
    content = content.replace('const panelOrder = [0, 1, 2, 3, 4, 5, 6, 6.5, 7];', 'const panelOrder = [0, 1, 2, 3, 4, 5, 6, 7];')
    
    # 6. Change triageView iframe to point to localhost:3000 if they want to load the React app?
    # Actually, they might not be running React. They just wanted the name changed. I already changed it to QuantaMed Pharmacovigilance.
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Done refactoring index.html!")

if __name__ == "__main__":
    main()
