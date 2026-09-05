from pathlib import Path
root=Path(__file__).resolve().parents[1]
required=['pyproject.toml','requirements.txt','main.py','backend/main.py','frontend/dist/index.html','frontend/dist/assets/app.js','frontend/dist/assets/app.css']
missing=[p for p in required if not (root/p).exists()]
if missing:
    raise SystemExit('Missing: '+', '.join(missing))
print('Fenix Messenger project: OK')
