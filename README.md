## Quick Start

### 1) Clone the repository

1. Clone the repository:

```bash
git clone <repo-url>
```

2. Move into the project folder:

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
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies from [requirements.txt](requirements.txt):

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2a) Install Tesseract OCR

This project uses OCR to read text from uploaded documents. The `pytesseract` Python package does not install the Tesseract binary, so you must install Tesseract separately.

Windows (end-to-end):

1. Download and install Tesseract from:
	https://github.com/UB-Mannheim/tesseract/wiki
2. Find the install folder. The default is typically:
	`C:\Program Files\Tesseract-OCR`
3. Add the folder to your PATH:

Option A: GUI

- Open Start Menu and search for "Environment Variables".
- Select "Edit the system environment variables".
- Click "Environment Variables...".
- Under "System variables", select `Path` and click "Edit...".
- Click "New" and add the Tesseract folder path.
- Click "OK" to save.


4. Open a new terminal and verify:

```powershell
tesseract --version
```

If you installed Tesseract elsewhere, replace the path in step 3 with the folder that contains `tesseract.exe`.

Linux (minimal):

```bash
sudo apt update
sudo apt install -y tesseract-ocr
```

### 2b) Configure Hugging Face API key (required)

The backend requires a Hugging Face API key. If it is missing, you will see:
"HuggingFace API key is required. Set HF_API_KEY or HUGGINGFACEHUB_API_TOKEN in .env"

1. Copy the example env file:
	`backend/.env.example` -> `backend/.env`
2. Add your key (use one line):

```env
HF_API_KEY="your_hf_api_key_here"
```

If you do not have an API key yet, create one at:
https://huggingface.co/settings/tokens

Windows PowerShell (optional alternative):

```powershell
setx HF_API_KEY "your_hf_api_key_here"
```

If you set it via `setx`, open a new terminal so the variable is available.

### 3) Run the project

Run these commands from the project root (the folder that contains `run_backend.py` and `run_frontend.py`).

1. Open Terminal 1 in the project root and start the backend (port 8001):

```bash
python run_backend.py
```

2. Open Terminal 2 in the same project root and start the frontend (port 5000):

```bash
python run_frontend.py
```


Open http://127.0.0.1:5000/ in your browser.
