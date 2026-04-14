# Perception study (Flask prototype)

## What this does

- **Flask** is a small Python web framework: it maps URLs to Python functions and returns HTML.
- **`trials.json`** lists trials. Each trial has a **center** (synthetic reference) and **four option** image filenames.
- **Static files** (images) live under `static/images/`. Flask serves them at `/static/images/<filename>`.
- **Session** (signed cookie) stores: randomized trial order, which trial you are on, and the shuffled order of the four options for each trial (so a refresh does not reshuffle mid-trial).
- **POST `/submit`** records one row to **`results.csv`** and redirects to the next trial.

## Setup (recommended: virtual environment)

```bash
cd /home/moon/csalditt/Documents/bacholorarbeit/perception_plantes
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Add images

Copy your PNG/JPG files into `static/images/` so filenames match `trials.json`. Until then, the page loads but images may appear broken.

## Run locally

```bash
cd /home/moon/csalditt/Documents/bacholorarbeit/perception_plantes
source .venv/bin/activate   # if you use venv
python app.py
```

Open **http://127.0.0.1:5000** in the browser.

## Phone on the same Wi‑Fi

Start the server bound to all interfaces and use your PC’s LAN IP from the phone:

```bash
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
python app.py
```

Then visit `http://<your-computer-ip>:5000` on the phone (same network as the PC).

## Output

- **`results.csv`** is created next to `app.py`. Each row: UTC timestamp, `trial_id`, center filename, chosen filename, clicked position (0–3), and the four option filenames in on-screen order (semicolon-separated).

## Security note for real studies

Set a random secret so sessions cannot be forged:

```bash
export FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

## Google Sheets (optional, not implemented)

This prototype only writes **CSV**. You can import `results.csv` into Sheets manually or add a later step (e.g. `gspread` with a service account).
