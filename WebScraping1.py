def scrape(uname=None, pwd=None, captcha_input=None, generate_captcha=False):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import NoSuchElementException
    from PIL import Image
    import time
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.common.action_chains import ActionChains

    # Set up the browser options
    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--ignore-certificate-errors")
    # options.add_argument("--headless")
    options.add_argument("no-sandbox")
    options.add_argument("disable-dev-shm-usage")
    
    # Create a global driver variable to maintain the session
    if 'driver' not in globals():
        globals()['driver'] = webdriver.Chrome(options=options)

    driver = globals()['driver']

    # Navigate to the login page
    driver.get("https://vtopcc.vit.ac.in/vtop/login")
    driver.find_element(By.ID, "stdForm").click()

    # If generate_captcha is True, only retrieve and save the CAPTCHA image
    if generate_captcha:
        try:
            captcha_image_element = driver.find_element(By.CSS_SELECTOR, ".form-control.img-fluid.bg-light.border-0")
            captcha_image_bytes = captcha_image_element.screenshot_as_png
            captcha_image_path = "static/captcha_temp.png"

            with open(captcha_image_path, "wb") as f:
                f.write(captcha_image_bytes)

            return captcha_image_path
        except NoSuchElementException:
            return None

    # If credentials and CAPTCHA are provided, continue with login
    if uname and pwd and captcha_input:
        driver.find_element(By.ID, "username").send_keys(uname)
        driver.find_element(By.ID, "password").send_keys(pwd)
        driver.find_element(By.ID, "captchaStr").send_keys(captcha_input)
        
        # Click login and wait for the page to load
        driver.find_element(By.ID, "submitBtn").click()
        time.sleep(3)

        try:
            driver.find_element(By.ID, "btnClosePopup").click()
        except NoSuchElementException:
            print("No popup to close.")

        # Continue with your timetable extraction code below...

        # Hover over the menu and select the timetable
        button_to_hover = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'SideBarMenuBtn')]/i[contains(@class, 'fa-graduation-cap')]"))
        )

        actions = ActionChains(driver)
        actions.move_to_element(button_to_hover).perform()

        time.sleep(1)

        # Click on the link to open the timetable
        link_element = driver.find_element(By.XPATH, "//a[@data-url='academics/common/StudentTimeTableChn']")
        link_element.click()

        # Select the semester from the dropdown
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "semesterSubId"))
        )
        sel = Select(select_element)
        sel.select_by_visible_text("Winter Semester 2023-24")

        time.sleep(2)
        # Initialize an empty list to hold the "Slot - Venue" data
        slot_venue_data = []

        # Locate the table inside the 'studentDetailsList' div
        table_element = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[1]/div/section/div/div/div[2]/div/div/div/div[3]/table")

        # Locate all the rows in the table's tbody
        rows = table_element.find_elements(By.XPATH, './/tbody/tr')
        b = []
        # Loop through each row and extract the "Slot - Venue" column data
        for row in range(4, len(rows)):
            try:
                a = rows[row].text.split()
                b.append(a)
            except NoSuchElementException:
                continue  # Handle cases where the column might not exist

        final = []
        for i in b:
            x = []
            for j in range(2, len(i)):
                if len(i[j]) <= 10:
                    x.append(0)
                else:
                    bui = i[j].split('-')[3]
                    if bui == "AB1":
                        x.append(1)
                    elif bui == "AB2":
                        x.append(3)
                    elif bui == "AB3":
                        x.append(2)
            if len(x) == 12:
                x.insert(6, 0)
            final.append(x)
        print(final)

        # Close the driver at the end of your scraping function
        return True  # Return True for successful login, adjust as needed

    return False  # If no login attempt was made
