import schedule
import time
import logging
from datetime import datetime
from fetch_data import fetch_and_store

# ── Log setup ──────────────────────────────────────────────────────────────
# This creates fetch_log.txt automatically in your project folder
logging.basicConfig(
    filename="fetch_log.txt",        # log file name (auto-created)
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def run_fetch():
    """Fetch data and write result to log file."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching stock data...")
    try:
        fetch_and_store()
        logging.info("SUCCESS - Stock data fetched and saved to stocks.db and stocks_data.csv")
        print("Fetch complete! Log updated.")
    except Exception as e:
        logging.error(f"FAILED - {str(e)}")
        print(f"Error: {e}")

# ── Run immediately when script starts ─────────────────────────────────────
print("Scheduler started. Fetching data now...")
run_fetch()

# ── Then auto-repeat every 4 hours ─────────────────────────────────────────
schedule.every(4).hours.do(run_fetch)

print("\nScheduler is running. It will auto-fetch every 4 hours.")
print("Press Ctrl + C to stop.\n")

while True:
    schedule.run_pending()
    time.sleep(60)   # check every 60 seconds if a job is due