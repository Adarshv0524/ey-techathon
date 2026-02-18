## Setup

### Prerequisites

- Python 3.10+ installed

### Install Python dependencies

All required Python libraries are listed in [requirements.txt](requirements.txt).

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

1. Start backend (port 8001):

```bash
python run_backend.py
```

2. Start frontend (port 5000) in another terminal:

```bash
python run_frontend.py
```

Open http://127.0.0.1:5000/.