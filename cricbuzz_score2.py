"""
Cricbuzz Live Score - a Streamlit app that uses Playwright to read the
live cricket score from cricbuzz.com and show it with a screenshot.

Run:
    streamlit run cricbuzz_score2.py
"""
import asyncio
import re
import sys

import streamlit as st
from streamlit import runtime

# Started with plain "python cricbuzz_score2.py" (e.g. the VS Code Run button)?
# Re-launch through Streamlit so the app opens in the browser.
if __name__ == "__main__" and not runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Windows: Playwright needs the Proactor event loop to start the browser.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

URL = "https://www.cricbuzz.com/"

# Every match card on Cricbuzz links to /live-cricket-scores/<id>/<slug>.
# Checked in DevTools: document.querySelectorAll('a[href*="/live-cricket-scores/"]')
MATCH_CARD = 'a[href*="/live-cricket-scores/"]'

# A score looks like "287-4 (45.2)" or "287/4 (45.2)".
SCORE_PATTERN = re.compile(r"\d{1,3}(?:[-/]\d{1,2})?\s*\(\d{1,2}(?:\.\d)?")

FINISHED_WORDS = ("won by", "drawn", "abandon", "no result", "tied")
UPCOMING_WORDS = ("starts", "preview", "match yet to begin", "tomorrow", "today,")

TIMEOUT_MS = 20_000          # max wait for the score; stops as soon as it appears
SCREENSHOT_PATH = "score.png"


def classify(text: str) -> str:
    """Return 'live', 'finished' or 'upcoming' for a match card's text."""
    low = text.lower()
    if any(w in low for w in FINISHED_WORDS):
        return "finished"
    if any(w in low for w in UPCOMING_WORDS) or not SCORE_PATTERN.search(text):
        return "upcoming"
    return "live"


def clean(text: str) -> str:
    """Remove blank lines and extra spaces."""
    return "\n".join(ln.strip() for ln in text.splitlines() if ln.strip())


def scrape(headless: bool = True) -> dict:
    """
    Open Cricbuzz, wait for the match cards, and return:
        {"status": "live" | "no_live" | "error",
         "score": str, "message": str, "screenshot": path or None}
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1366, "height": 900})

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            # Waits for the element itself instead of a fixed sleep(5).
            page.wait_for_selector(MATCH_CARD, state="visible", timeout=TIMEOUT_MS)
        except PlaywrightTimeout:
            page.screenshot(path=SCREENSHOT_PATH)
            browser.close()
            return {
                "status": "error",
                "score": "",
                "message": "No match cards appeared. Cricbuzz may be slow or its layout changed.",
                "screenshot": SCREENSHOT_PATH,
            }

        cards = page.locator(MATCH_CARD)
        live_card = live_text = first_card = first_text = None

        for i in range(cards.count()):
            card = cards.nth(i)
            if not card.is_visible():
                continue
            text = clean(card.inner_text())
            if not text:
                continue
            if first_card is None:
                first_card, first_text = card, text
            if classify(text) == "live":
                live_card, live_text = card, text
                break

        if live_card is not None:
            target = live_card
            result = {"status": "live", "score": live_text, "message": "Live match found."}
        else:
            target = first_card
            result = {
                "status": "no_live",
                "score": first_text or "",
                "message": "No match is live right now. Showing the latest match.",
            }

        try:
            target.scroll_into_view_if_needed()
            target.screenshot(path=SCREENSHOT_PATH)
        except Exception:
            page.screenshot(path=SCREENSHOT_PATH)

        browser.close()
        result["screenshot"] = SCREENSHOT_PATH
        return result


# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Cricbuzz Live Score", page_icon="🏏")
st.title("🏏 Cricbuzz Live Score")
st.write("Opens cricbuzz.com in a real browser with Playwright, waits for the "
         "score to load, and shows it here with a screenshot.")

headed = st.checkbox("Show the browser while scraping (headed mode)", value=False)

if st.button("Get live score", type="primary"):
    with st.spinner("Opening Cricbuzz and waiting for the score..."):
        try:
            result = scrape(headless=not headed)
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.stop()

    if result["status"] == "live":
        st.success(result["message"])
    elif result["status"] == "no_live":
        st.warning(result["message"])
    else:
        st.error(result["message"])

    if result["score"]:
        st.subheader("Score")
        st.code(result["score"], language=None)
        print(result["score"])  # also print to the terminal

    if result.get("screenshot"):
        st.image(result["screenshot"], caption="saved score.png")
