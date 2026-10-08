import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

os.makedirs("static/img/help", exist_ok=True)

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,900")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    print("Navigating to signin page...")
    driver.get("http://127.0.0.1:8000/signin/")
    time.sleep(1.5)

    email_input = driver.find_element(By.NAME, "email")
    password_input = driver.find_element(By.NAME, "password")
    
    email_input.send_keys("admin@mytts.org")
    password_input.send_keys("admin123")
    
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()
    time.sleep(2.5)

    print("Logged in. Current URL:", driver.current_url)

    pages = {
        "dashboard.png": "http://127.0.0.1:8000/menu/admin/dashboard",
        "students_list.png": "http://127.0.0.1:8000/menu/admin/students/",
        "assign_books.png": "http://127.0.0.1:8000/menu/admin/students/student-books/",
        "assign_subjects.png": "http://127.0.0.1:8000/menu/admin/students/student-subjects/",
        "assign_exams.png": "http://127.0.0.1:8000/menu/admin/students/student-exams",
        "submitted_exams.png": "http://127.0.0.1:8000/menu/admin/students/student-submitted-exams/",
        "exams_list.png": "http://127.0.0.1:8000/menu/admin/exams",
        "exam_create.png": "http://127.0.0.1:8000/menu/exams/create/",
        "student_requests.png": "http://127.0.0.1:8000/menu/admin/applications/",
        "payments_list.png": "http://127.0.0.1:8000/menu/admin/payments/",
        "pages_list.png": "http://127.0.0.1:8000/menu/admin/pages/",
        "page_create.png": "http://127.0.0.1:8000/menu/pages/create/",
        "menus_list.png": "http://127.0.0.1:8000/menu/admin/menus/",
        "menu_engineer.png": "http://127.0.0.1:8000/menu/menus/engineer/",
        "media_list.png": "http://127.0.0.1:8000/menu/admin/media/",
        "categories_list.png": "http://127.0.0.1:8000/menu/admin/categories",
        "courses_list.png": "http://127.0.0.1:8000/menu/admin/courses/",
        "roles_list.png": "http://127.0.0.1:8000/menu/admin/roles",
        "code_settings.png": "http://127.0.0.1:8000/menu/admin/codes/",
        "support_list.png": "http://127.0.0.1:8000/menu/admin/support",
        "users_list.png": "http://127.0.0.1:8000/menu/admin/users/",
        "church_codes.png": "http://127.0.0.1:8000/menu/admin/church-codes",
        "church_admin_apps.png": "http://127.0.0.1:8000/menu/admin/church-admin-applications/",
    }

    for filename, url in pages.items():
        try:
            print(f"Capturing {filename} from {url}...")
            driver.get(url)
            time.sleep(1.5)
            filepath = os.path.join("static/img/help", filename)
            driver.save_screenshot(filepath)
            print(f"Saved {filepath} ({os.path.getsize(filepath)} bytes)")
        except Exception as e:
            print(f"Error capturing {filename}: {e}")

finally:
    driver.quit()
