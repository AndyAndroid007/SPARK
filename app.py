from flask import Flask, render_template, request, flash, redirect, url_for, send_file, session
from flask import render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import urllib3
from flask import jsonify
import numpy as np
from datetime import datetime
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your_secret_key'  # Required for flashing messages

# Global variable to hold the WebDriver instance
driver = None

def create_driver():
    # Set up the browser options
    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--ignore-certificate-errors")
    #options.add_argument("--headless")
    options.add_argument("no-sandbox")
    options.add_argument("disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def is_driver_active(driver):
    try:
        driver.current_url  # Attempt to retrieve the current URL
        return True
    except Exception:
        return False

def retrieve_captcha():
    global driver
    if not is_driver_active(driver):
        driver = create_driver()
    
    driver.get("https://vtopcc.vit.ac.in/")
    driver.minimize_window()
    driver.find_element(By.ID, "stdForm").click()
    
    try:
        # Retrieve and save the CAPTCHA image
        captcha_image_element = driver.find_element(By.CSS_SELECTOR, ".form-control.img-fluid.bg-light.border-0")
        captcha_image_bytes = captcha_image_element.screenshot_as_png
        captcha_image_path = "static/captcha_temp.png"

        with open(captcha_image_path, "wb") as f:
            f.write(captcha_image_bytes)

        return captcha_image_path
    except NoSuchElementException:
        return retrieve_captcha()
import numpy as np

def weighted_average_priority(schedule):
    # Define weights for a 13-element schedule, prioritizing earlier classes
    weights = [0.25, 0.2, 0.15, 0.1, 0.08, 0.05, 0.05, 0.04, 0.03, 0.02, 0.02, 0.01, 0.01]
    
    # Ensure the schedule has exactly 13 classes
    assert len(schedule) == len(weights), "Schedule array must be exactly 13 elements long."
    
    # Filter out classes with no schedule (value 0) and corresponding weights
    non_zero_schedule = [val for val in schedule if val != 0]
    non_zero_weights = [weights[i] for i in range(len(schedule)) if schedule[i] != 0]

    # Calculate weighted average for only non-zero schedule items
    weighted_values = np.multiply(non_zero_schedule, non_zero_weights)
    weighted_avg = sum(weighted_values) / sum(non_zero_weights)
    
    # Round to the nearest building number
    return round(weighted_avg)

def recommend_parking(day_schedule):
    weighted_avg = weighted_average_priority(day_schedule)
    
    # Recommendation logic based on weighted average
    if weighted_avg == 1:
        return ["Parking 1", "Parking 2", "Parking 3"]
    elif weighted_avg == 2:
        return ["Parking 2", "Parking 1", "Parking 3"]
    else:
        return ["Parking 3", "Parking 1", "Parking 2"]

def scrape(driver, uname, pwd, captcha_input):
    try:
        # Check if the driver is still active
        if not is_driver_active(driver):
            driver = create_driver()
            driver.get("https://vtopcc.vit.ac.in/")
        
        # Enter credentials and CAPTCHA, then log in
        driver.find_element(By.ID, "username").send_keys(uname)
        driver.find_element(By.ID, "password").send_keys(pwd)
        driver.find_element(By.ID, "captchaStr").send_keys(captcha_input)
        
        # Click login and wait for the page to load
        driver.find_element(By.ID, "submitBtn").click()
        time.sleep(3)
        
        # Check for login errors
        if driver.current_url == "https://vtopcc.vit.ac.in/vtop/login/error":
            flash("Invalid credentials or CAPTCHA. Try again!")
            driver.quit()
            driver = None
            return False

        # Handle popups if present
        try:
            driver.find_element(By.ID, "btnClosePopup").click()
        except NoSuchElementException:
            print("No popup to close.")

        # Continue with extracting the timetable
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

        # Extract the timetable data
        table_element = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/div[1]/div[1]/div[2]/div[1]/div[1]/div/section/div/div/div[2]/div/div/div/div[3]/table")
        rows = table_element.find_elements(By.XPATH, './/tbody/tr')
        
        b = []
        for row in range(4, len(rows)):
            try:
                a = rows[row].text.split()
                b.append(a)
            except NoSuchElementException:
                continue

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
        
        
        print(final[2])
        print(1)
        combined_final = []
        for i in range(0, len(final), 2):
            combined_day = [max(a, b) for a, b in zip(final[i], final[i + 1])]
            combined_final.append(combined_day)
        
        print(combined_final)
        # Recommend parking based on the timetable
        today = datetime.today().weekday()
        print(today)
        recommended_parking = recommend_parking(combined_final[0])
        print(recommended_parking)
        print(2)
        
                

        return True, recommended_parking

    except urllib3.exceptions.MaxRetryError:
        flash("Session expired or connection failed, retrying...")
        driver.quit()
        driver = None
        return False, None

    except Exception as e:
        flash(f"Error during login: {e}")
        if driver:
            driver.quit()
            driver = None
        return False, None

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    global driver
    global captcha_image_path

    if driver is None:
        driver = create_driver()  # Create the driver session on the first request

    if request.method == 'POST':
        uname = request.form["username"]
        pwd = request.form["password"]
        captcha_input = request.form["captcha"]

        if not uname or not pwd or not captcha_input:
            flash("Enter proper credentials and solve the CAPTCHA!")
            return redirect(url_for('login'))

        # Call the scrape function with the provided credentials and CAPTCHA
        success, recommended_parking = scrape(driver, uname, pwd, captcha_input)
        if success:
            flash("Login successful!")
            session['recommended_parking'] = recommended_parking
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))

    # Generate the CAPTCHA image when the page loads for the first time
    captcha_image_path = retrieve_captcha()

    return render_template('login.html', captcha_image=captcha_image_path)

@app.route('/captcha_image')
def captcha_image():
    return send_file('static/captcha_temp.png', mimetype='image/png')

@app.route('/home')
def home():
    recommended_parking = session.get('recommended_parking', [])
    return render_template('main.html', recommended_parking=recommended_parking)
@app.route('/parking/<int:parking_id>')
def parking(parking_id):
    # Retrieve data based on the parking_id (you can use a database query here)
    parking_data = get_parking_data(parking_id)
    return render_template('parking.html', parking_data=parking_data)

parking_lots = {
    1: {'name': 'Student Parking Lot', 'value': 60, 'lat': 12.841464792292294, 'lng': 80.15312097900434, 'in': 0, 'out': 0},
    2: {'name': 'MG Auditorium Parking', 'value': 80, 'lat': 12.840513143394107, 'lng': 80.15519510555724, 'in': 0, 'out': 0},
    3: {'name': 'Parking Lot 3', 'value': 40, 'lat': 12.841596965464273, 'lng': 80.15200031804777, 'in': 0, 'out': 0}
}
@app.route('/update_counts/<int:parking_id>', methods=['POST'])
def update_counts(parking_id):
    data = request.get_json()
    parking_lot = parking_lots.get(parking_id)
    if parking_lot:
        # Update the in and out counts
        parking_lot['in'] = data.get('in', parking_lot['in'])
        parking_lot['out'] = data.get('out', parking_lot['out'])
        return jsonify({"message": "Counts updated"}), 200
    return jsonify({"error": "Parking lot not found"}), 404

# Example function to get parking data (replace with actual database call)
def get_parking_data(parking_id):
    parking_lot = parking_lots.get(parking_id, {})
    if parking_lot:
        # Adjust the available spots calculation
        parking_lot['available_spots'] = parking_lot['value'] - parking_lot['in'] + parking_lot['out']
    return parking_lot


@app.route('/logout')
def logout():
    global driver
    if driver is not None:
        driver.quit()  # Close the driver on logout
        driver = None  # Reset the driver variable
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
