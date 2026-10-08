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
    driver.find_element(By.NAME, "password").submit()
    time.sleep(2)

    print("Navigating to Dashboard...")
    driver.get("http://127.0.0.1:8000/menu/admin/dashboard")
    time.sleep(1.5)

    # Find Help button in top bar right
    topbar_help_btn = driver.find_element(By.CSS_SELECTOR, "a.help-topbar-btn")
    print("Found topbar Help button:", topbar_help_btn.text)
    
    topbar_help_btn.click()
    time.sleep(2)
    print("URL after clicking topbar Help button:", driver.current_url)

finally:
    driver.quit()
