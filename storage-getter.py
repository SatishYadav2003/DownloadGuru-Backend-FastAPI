import time
import json
import random
from playwright.sync_api import sync_playwright

EMAIL = "crce.9939.ce@gmail.com"
PASSWORD = "crce.9939.ce@7769030868"
STORAGE_FILE = "storage.json"

def human_delay(min_ms=80, max_ms=180):
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

def slow_type(element, text):
    for char in text:
        element.type(char, delay=random.randint(100, 200))
        human_delay()

def automated_login_and_save_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to Google sign-in page...")
        page.goto("https://accounts.google.com/signin/v2/identifier", timeout=60000)

        print("Typing email...")
        email_input = page.wait_for_selector("input[type='email']")
        email_input.click()
        slow_type(email_input, EMAIL)
        human_delay()
        next_btn = page.locator("button:has-text('Next')")
        next_btn.hover()
        next_btn.click()

        # Step 2: Enter password
        print("Waiting for password field...")
        page.wait_for_load_state('networkidle', timeout=15000)
        password_input = page.wait_for_selector("input[type='password']", timeout=15000)
        password_input.click()
        print("Typing password...")
        slow_type(password_input, PASSWORD)
        human_delay()
        pass_btn = page.locator("button:has-text('Next')")
        pass_btn.hover()
        pass_btn.click()

        print("Waiting for login to complete...")
        page.wait_for_timeout(8000)

        page.goto("https://www.youtube.com", timeout=60000)
        print("YouTube title:", page.title())

        # Save session
        context.storage_state(path=STORAGE_FILE)
        print(f"\u2705 Session saved to {STORAGE_FILE}")
        browser.close()



if __name__ == "__main__":
    automated_login_and_save_session()
   
