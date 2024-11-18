def scrape(uname,pwd):

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import NoSuchElementException
    from PIL import Image
    import time
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select




    # Set up the browser options
    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless")
    options.add_argument("no-sandbox")
    options.add_argument("disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    # Navigate to the login page
    driver.get("https://vtopcc.vit.ac.in/vtop/login")
    driver.find_element(By.ID, "stdForm").click()

    # Login details
    username = "21BCE1270"
    password = "Fraudvit*69"

    # Function to handle CAPTCHA
    def solve_captcha():
        while True:
            try:
                # Re-enter username and password after each refresh
                driver.find_element(By.ID, "username").clear()
                driver.find_element(By.ID, "username").send_keys(username)
                driver.find_element(By.ID, "password").clear()
                driver.find_element(By.ID, "password").send_keys(password)
                
                # Check if reCAPTCHA iframe exists
                recaptcha_iframe = driver.find_element(By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")
                print("reCAPTCHA found. Reloading the page...")
                
                # Reload the page if reCAPTCHA is found
                driver.refresh()
                time.sleep(3)
            
            except NoSuchElementException:
                try:
                    # Check if image CAPTCHA exists
                    captcha_image_element = driver.find_element(By.CSS_SELECTOR, ".form-control.img-fluid.bg-light.border-0")
                    
                    # If image CAPTCHA exists, save it and ask user to solve
                    print("Image CAPTCHA found. Please solve it.")
                    captcha_image_bytes = captcha_image_element.screenshot_as_png
                    captcha_image_path = "captcha_temp.png"
                    
                    with open(captcha_image_path, "wb") as f:
                        f.write(captcha_image_bytes)
                    
                    captcha_image = Image.open(captcha_image_path)
                    captcha_image.show()
                    
                    # Get the CAPTCHA input from the user
                    captcha_input = input("Please enter the CAPTCHA displayed in the image: ")
                    driver.find_element(By.ID, "captchaStr").send_keys(captcha_input)
                    break  # Break the loop once CAPTCHA is solved

                except NoSuchElementException:
                    print("No CAPTCHA found. Proceeding without CAPTCHA.")
                    break

    # Call the CAPTCHA solving function
    solve_captcha()

    # Click login
    driver.find_element(By.ID, "submitBtn").click()
    time.sleep(3)

    # Close any popups
    try:
        driver.find_element(By.ID, "btnClosePopup").click()
    except NoSuchElementException:
        print("No popup to close.")

    # Continue with your timetable extraction code below...

    # Close any popups



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

    # Locate the table inside the 'studentDetailsList' div using the full XPath you provided
    table_element = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[1]/div/section/div/div/div[2]/div/div/div/div[3]/table")

    # Locate all the rows in the table's tbody
    rows = table_element.find_elements(By.XPATH, './/tbody/tr')
    b=[]
    # Loop through each row and extract the "Slot - Venue" column data
    for row in range(4,len(rows)):
        try:
            # Access the 8th column in the current row
            # slot_venue = row.find_element(By.XPATH, './td[1]').text
            # slot_venue_data.append(slot_venue)
            a = rows[row].text.split()
            b.append(a)
        except NoSuchElementException:
            continue  # Handle cases where the 8th column might not exist

    # Close the WebDriver
    driver.quit()
    final = []

    for i in b:
        x = []
        for j in range(2,len(i)):
            if len(i[j])<=10:
                x.append(0)
            else:
                bui = i[j].split('-')[3]
                if(bui == "AB1"):
                    x.append(1)
                elif(bui == "AB2"):
                    x.append(3)
                elif(bui == "AB3"):
                    x.append(2)
        if(len(x)==12):
            x.insert(6,0)
        final.append(x)
    return final
        

