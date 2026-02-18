## Quick Start

### 1) Fork and clone

1. Fork this repository in GitHub.
2. Copy your fork URL and clone it:

```bash
git clone <your-fork-url>
```

3. Move into the project folder:

```bash
cd ey-techathon
```

### 2) Set up Python

Prerequisite: Python 3.10+ installed.

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

2. Install dependencies from [requirements.txt](requirements.txt):

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2a) Install Tesseract OCR

This project uses OCR to read text from uploaded documents. The `pytesseract` Python package needs the Tesseract system binary installed.

Windows:

1. Download and install Tesseract from:
	https://github.com/UB-Mannheim/tesseract/wiki
2. Ensure the install folder (for example, `C:\Program Files\Tesseract-OCR`) is added to your PATH.

Linux (minimal):

```bash
sudo apt update
sudo apt install -y tesseract-ocr
```

### 3) Run the project

1. Start the backend (port 8001):

```bash
python run_backend.py
```

2. In another terminal, start the frontend (port 5000):

```bash
python run_frontend.py
```

Open http://127.0.0.1:5000/ in your browser.