import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,900")

driver = webdriver.Chrome(options=options)

try:
    print("Logging in...")
    driver.get("http://127.0.0.1:8000/signin/")
    time.sleep(1.5)

    driver.find_element(By.NAME, "email").send_keys("admin@mytts.org")
    driver.find_element(By.NAME, "password").send_keys("admin123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)

    print("Navigating to http://127.0.0.1:8000/menu/admin/help/...")
    driver.get("http://127.0.0.1:8000/menu/admin/help/")
    time.sleep(2)

    print("Page title:", driver.title)
    print("Page source contains 'Admin Panel Documentation':", "Admin Panel Documentation" in driver.page_source)
    print("Page source contains 'Pages & Website Content Management':", "Pages & Website Content Management" in driver.page_source)
    print("Page source contains 'Menu Management':", "Menu Management" in driver.page_source)

    # Take screenshot of Help page itself
    driver.save_screenshot("static/img/help/help_page_full.png")
    print("Saved screenshot of help page to static/img/help/help_page_full.png")

finally:
    driver.quit()
