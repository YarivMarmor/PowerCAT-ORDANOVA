@echo off
python -m pip install -e ".[dev]"
python -m pytest -q
python -m PyInstaller --noconfirm --clean --onefile --windowed --name PowerCAT_ORDANOVA --paths src run_app.py
pause
