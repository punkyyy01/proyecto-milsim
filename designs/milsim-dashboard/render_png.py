from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
HTML = (HERE / 'index.html').resolve()
OUT = HERE / f'milsim_peloton_{int(__import__('time').time())}.png'

def render():
    url = HTML.as_uri()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={"width":1200, "height":900}, device_scale_factor=2)
        page = context.new_page()
        page.goto(url)
        page.wait_for_selector('#mainWork', timeout=10000)
        el = page.locator('#mainWork')
        el.screenshot(path=str(OUT))
        browser.close()
    print('Saved:', OUT)

if __name__ == '__main__':
    render()
