# Cricbuzz Live Score

A Streamlit app that captures the live cricket score from [Cricbuzz](https://www.cricbuzz.com/) using Playwright.

A live score isn't in the downloaded HTML; JavaScript loads it afterwards. Playwright drives a real Chromium browser, so it sees the page just as you do.

## What it does

1. Click **Get live score** in the app.
2. Playwright opens cricbuzz.com and waits for the match cards to appear. It uses `wait_for_selector` instead of a fixed `sleep()`, so it continues as soon as the score loads.
3. It finds the first **live** match and shows the score in the app. The score is also printed to the terminal.
4. It saves a screenshot of the match as `score.png` and shows it in the app.
5. If no match is live, it doesn't crash. It says so and shows the latest match instead.

## Selector

```css
a[href*="/live-cricket-scores/"]
```

Each match card on Cricbuzz links to `/live-cricket-scores/<id>/<match>`. This link pattern is more stable than CSS class names. You can check it in the browser console:

```js
document.querySelectorAll('a[href*="/live-cricket-scores/"]')
```

## Requirements

- Python 3.9+
- `playwright`
- `streamlit`

## Setup

```bash
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
streamlit run cricbuzz_score2.py
```

The app opens at http://localhost:8501. To watch the browser work, tick **Show the browser while scraping (headed mode)**. Leave it unticked to run headless.

## Files

| File | Purpose |
|------|---------|
| `cricbuzz_score2.py` | The Streamlit app and the Playwright scraper |
| `requirements.txt` | Python packages |
| `score.png` | Screenshot saved after each run |
