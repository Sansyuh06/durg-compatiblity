import re

file_path = r"d:\fyeshi\project\quantum\shiva vro\drug-triage-env\server\quantamed\index.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Hardcore Noir CSS overrides
noir_css = """
/* STRICT NOIR OVERRIDES */
body {
    background-color: #03060f !important;
    background-image: radial-gradient(circle at center, rgba(255,255,255,0.03) 1px, transparent 1px) !important;
    background-size: 24px 24px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: #e8f0fe !important;
}

header {
    background: rgba(3,6,15,0.92) !important;
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    backdrop-filter: blur(20px) !important;
    box-shadow: none !important;
}

.mode-tabs {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 0 !important;
    margin-bottom: 40px !important;
}

.mode-tab {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #3a5070 !important;
}

.mode-tab.active {
    color: #00d4e6 !important;
    border-bottom: 2px solid #00d4e6 !important;
}

.step-nav {
    gap: 0 !important;
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    padding-bottom: 0 !important;
}

.step-btn {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    color: #3a5070 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    box-shadow: none !important;
    transform: none !important;
    padding: 12px 16px !important;
}

.step-btn:first-child {
    border-left: 1px solid rgba(255,255,255,0.05) !important;
}

.step-btn.active {
    background: rgba(0, 212, 230, 0.05) !important;
    color: #00d4e6 !important;
    border-top: 1px solid #00d4e6 !important;
}

.step-btn:hover {
    transform: none !important;
    background: rgba(255,255,255,0.02) !important;
}

.panel {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 4px !important;
    box-shadow: none !important;
}

.section-title {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important;
    letter-spacing: 0.15em !important;
    color: #3a5070 !important;
    text-transform: uppercase !important;
}

.main-title {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    color: #e8f0fe !important;
    font-size: 24px !important;
}

.main-title span {
    color: #00d4e6 !important;
}

.stat-card {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 4px !important;
    box-shadow: none !important;
}

.stat-label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important;
    letter-spacing: 0.1em !important;
    color: #3a5070 !important;
    text-transform: uppercase !important;
}

.stat-value {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

button {
    border-radius: 3px !important;
}

.run-btn {
    background: #00d4e6 !important;
    color: #03060f !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 3px !important;
    box-shadow: none !important;
}

/* Fix missing tabs visually if they are hidden behind header */
.app {
    margin-top: 80px !important;
}
"""

if "/* STRICT NOIR OVERRIDES */" not in content:
    content = content.replace("</style>", noir_css + "\n</style>")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected strict Noir CSS into legacy app.")
else:
    print("Strict Noir CSS already present.")
