import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,900")

driver = webdriver.Chrome(options=options)

try:
    driver.get("http://127.0.0.1:8000/signin/")
    time.sleep(1.5)

    driver.find_element(By.NAME, "email").send_keys("admin@mytts.org")
    driver.find_element(By.NAME, "password").send_keys("admin123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)

    driver.get("http://127.0.0.1:8000/menu/admin/help/")
    time.sleep(2)

    print("Title:", driver.title)
    print("Contains Menu Management:", "Menu Management & Menu Engineer" in driver.page_source)
    print("Contains Form Fields Breakdown:", "Form Fields & Input Parameters" in driver.page_source)

finally:
    driver.quit()
