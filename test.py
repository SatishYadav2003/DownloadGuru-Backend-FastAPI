from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def get_youtube_headers_and_cookies():
    headers_for_ytdlp = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                geolocation={"latitude": 28.6139, "longitude": 77.2090},
                permissions=["geolocation"]
            )
            page = context.new_page()
            page.goto("https://www.youtube.com", wait_until="networkidle")

            # Make sure page is fully loaded before evaluate
            page.wait_for_load_state("load")

            # Get cookies
            cookies = context.cookies()
            cookie_string = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

            # Evaluate userAgent and accept-language safely
            try:
                user_agent = page.evaluate("() => navigator.userAgent")
            except Exception:
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

            try:
                accept_language = page.evaluate("() => navigator.language")
            except Exception:
                accept_language = "en-US,en;q=0.9"

            headers_for_ytdlp = {
                "User-Agent": user_agent,
                "Accept-Language": accept_language,
                "Cookie": cookie_string
            }

    except PlaywrightTimeoutError:
        print("Page load timed out.")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return headers_for_ytdlp


if __name__ == "__main__":
    headers = get_youtube_headers_and_cookies()
    print(headers)
