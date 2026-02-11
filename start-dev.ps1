# --- FastAPI backend ---
Start-Process powershell -ArgumentList @"
cd D:jeevitam\farmai
.\venv\Scripts\Activate.ps1
python -m app.main
"@

# --- React frontend ---
Start-Process powershell -ArgumentList @"
cd D:\reactJS\farm_sample_one
npm run dev
"@