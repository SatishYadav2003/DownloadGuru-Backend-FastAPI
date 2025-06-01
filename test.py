from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def login_and_save_cookies(email, password, cookies_path='cookies.txt'):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Show browser for manual 2FA if needed
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        # Go to Google login page
        page.goto("https://accounts.google.com/signin/v2/identifier")

        # Enter email
        page.wait_for_selector('input[type="email"]', timeout=10000)
        page.fill('input[type="email"]', "")
        for char in email:
            page.keyboard.insert_text(char)
        page.click('button:has-text("Next")')

        # Enter password
        page.wait_for_selector('input[type="password"]', timeout=10000)
        page.fill('input[type="password"]', "")
        for char in password:
            page.keyboard.insert_text(char)
        page.click('button:has-text("Next")')

        # Wait for navigation after login (handle 2FA if it appears)
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
            print("Logged in successfully!")
        except PlaywrightTimeoutError:
            print("Page did not finish loading in time after login; check for 2FA or additional steps.")

        # Navigate to YouTube to get YouTube-specific cookies
        page.goto("https://www.youtube.com")
        page.wait_for_load_state("networkidle", timeout=20000)
        print("Navigated to YouTube, ready to get cookies.")

        # Extract cookies from the browser context
        cookies = context.cookies()

        # Convert cookie list to "name=value; name2=value2; ..." string format
        cookie_string = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

        # Save cookies to file
        with open(cookies_path, 'w') as f:
            f.write(cookie_string)

        print(f"Cookies saved in netcat format to {cookies_path}")

        browser.close()

# Example usage:
login_and_save_cookies('crce.9939.ce@gmail.com', 'crce.9939.ce@7769030868')
