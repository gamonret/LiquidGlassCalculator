# Liquid Glass Calculator

A desktop calculator for Windows, built with Python and PySide6, featuring a translucent "Liquid Glass" interface.

## Features

- Dark and light themes
- Frameless, draggable window
- Keyboard input (digits, arithmetic operators, Enter, Backspace, Delete and Escape)
- Repeated calculation when pressing `=` again
- Basic arithmetic, percentages, sign toggle and decimal input

## Run from source

1. Install Python 3.10 or later.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Start the calculator:

   ```bash
   python calculator.py
   ```

## Windows executable

The Windows build is named `LiquidGlassCalculator.exe`. The EXE is about 46 MB; this repository currently contains the Python source. Upload the EXE as a GitHub Release asset or with Git LFS to avoid bloating regular Git history.

## Build your own EXE

```bash
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name LiquidGlassCalculator calculator.py
```
