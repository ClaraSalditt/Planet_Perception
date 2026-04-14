"""
Minimal Flask app for a 4AFC (four-alternative forced choice) perception study.

Concepts:
- Flask serves HTML pages and handles form posts.
- trials.json defines each trial: synthetic center image + 4 candidate filenames.
- Images live under static/images/ and are referenced with url_for('static', ...).
- The browser session stores: shuffled trial order, current position, and shuffled
  option order per trial_id (so refreshes keep the same layout until you advance).
- Answers append to results.csv (no database).
"""

import csv
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
# Needed for signed cookies (session). Use a strong random value in production.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")

BASE_DIR = Path(__file__).resolve().parent
TRIALS_FILE = BASE_DIR / "trials.json"
RESULTS_FILE = BASE_DIR / "results.csv"


def load_trials() -> List[Dict[str, Any]]:
    with TRIALS_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("trials.json must be a JSON array of trial objects.")
    return data


def ensure_session_trials(trials: List[Dict[str, Any]]) -> None:
    """Randomize trial order once per session."""
    if "trial_order" in session:
        return
    order = list(range(len(trials)))
    random.shuffle(order)
    session["trial_order"] = order
    session["current_idx"] = 0


def current_trial_view(
    trials: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], Optional[List[str]], int, int]:
    """
    Returns (trial_dict, shuffled_options, current_number_1based, total)
    or (None, None, total, total) if done.
    """
    ensure_session_trials(trials)
    order = session["trial_order"]
    idx = session.get("current_idx", 0)
    total = len(order)
    if idx >= total:
        return None, None, total, total
    trial = trials[order[idx]]
    tid = str(trial["trial_id"])
    key = f"opt_order_{tid}"
    if key not in session:
        opts = list(trial["options"])
        random.shuffle(opts)
        session[key] = opts
    options = session[key]
    current_num = idx + 1
    return trial, options, current_num, total


@app.route("/", methods=["GET"])
def index():
    trials = load_trials()
    trial, options, current_num, total = current_trial_view(trials)
    if trial is None:
        return render_template(
            "index.html",
            done=True,
            trial=None,
            options=None,
            current_num=total,
            total=total,
        )
    return render_template(
        "index.html",
        done=False,
        trial=trial,
        options=options,
        current_num=current_num,
        total=total,
    )


@app.route("/submit", methods=["POST"])
def submit():
    trials = load_trials()
    ensure_session_trials(trials)
    order = session["trial_order"]
    idx = session.get("current_idx", 0)
    if idx >= len(order):
        return redirect(url_for("index"))

    position_str = request.form.get("position")
    if position_str is None:
        return redirect(url_for("index"))
    try:
        clicked_position = int(position_str)
    except ValueError:
        return redirect(url_for("index"))
    if clicked_position not in (0, 1, 2, 3):
        return redirect(url_for("index"))

    trial = trials[order[idx]]
    tid = str(trial["trial_id"])
    key = f"opt_order_{tid}"
    options = session.get(key) or list(trial["options"])
    if len(options) != 4 or clicked_position >= len(options):
        return redirect(url_for("index"))

    chosen = options[clicked_position]
    center = trial["center"]
    option_order_str = ";".join(options)

    ts = datetime.now(timezone.utc).isoformat()
    write_header = not RESULTS_FILE.exists()
    with RESULTS_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(
                [
                    "timestamp_utc",
                    "trial_id",
                    "center_image",
                    "chosen_image",
                    "clicked_position",
                    "option_order",
                ]
            )
        w.writerow([ts, tid, center, chosen, clicked_position, option_order_str])

    session["current_idx"] = idx + 1
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Local development: http://127.0.0.1:5000 — use 0.0.0.0 to reach from phone on same Wi‑Fi.
    app.run(host=os.environ.get("FLASK_HOST", "127.0.0.1"), port=int(os.environ.get("FLASK_PORT", "5000")), debug=True)
