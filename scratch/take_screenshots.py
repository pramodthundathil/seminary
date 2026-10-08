import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,900")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    print("Navigating to login...")
    driver.get("http://127.0.0.1:8000/")
    time.sleep(2)
    print("Page title:", driver.title)
    print("Current URL:", driver.current_url)
finally:
    driver.quit()
