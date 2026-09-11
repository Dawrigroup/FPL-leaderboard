"""
Renders journal.html in a headless browser and saves a screenshot of the
#sheet element as journal.png. Runs a tiny local web server first so the
page's fetch('data.json') call works (file:// URLs block fetch via CORS).
"""
import http.server
import socketserver
import threading
import time

from playwright.sync_api import sync_playwright

PORT = 8791


def serve():
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    httpd.serve_forever()


def main():
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 450, "height": 950})
        page.goto(f"http://localhost:{PORT}/journal.html", wait_until="networkidle")

        # Wait for either the recap content or the "no recap yet" message,
        # so we don't screenshot the "loading..." placeholder.
        page.wait_for_selector(".recap-hero, .msg", timeout=15000)
        page.wait_for_timeout(400)

        page.locator("#sheet").screenshot(path="journal.png")
        browser.close()

    print("Saved journal.png")


if __name__ == "__main__":
    main()
