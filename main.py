

import time
import random
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


USERNAME = ""   # ← your Instagram username/email/phone
PASSWORD = ""   # ← your Instagram password
HEADLESS  = False



def human_sleep(min_s=1.5, max_s=3.5):
    time.sleep(random.uniform(min_s, max_s))


def init_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def login(driver, username, password):
    print(" Logging in to Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")
    wait = WebDriverWait(driver, 20)

    try:
        cookie_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Allow') or contains(text(),'Accept')]")
        ))
        cookie_btn.click()
        human_sleep()
    except:
        pass

    user_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    user_field.clear()
    user_field.send_keys(username)
    human_sleep(0.5, 1)

    pass_field = driver.find_element(By.NAME, "pass")
    pass_field.clear()
    pass_field.send_keys(password)
    human_sleep(0.5, 1)
    pass_field.send_keys(Keys.RETURN)

    wait.until(EC.url_contains("instagram.com"))
    human_sleep(3, 5)

    try:
        not_now = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Not Now') or contains(text(),'Not now')]")
        ))
        not_now.click()
        human_sleep()
    except:
        pass

    try:
        not_now2 = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Not Now') or contains(text(),'Not now')]")
        ))
        not_now2.click()
        human_sleep()
    except:
        pass

    print("Logged in successfully!")


def go_to_profile(driver, username):
    print(f"\n Going to profile page...")
    driver.get(f"https://www.instagram.com/{username}/")
    human_sleep(2, 4)
    print("On profile page!")


def find_scroll_container(driver):
    """Find the actual scrollable list inside the modal."""
    
    candidates = [
        "//div[@role='dialog']//div[contains(@class,'x6nl9eh')]",
        "//div[@role='dialog']//div[contains(@style,'overflow') and contains(@style,'auto')]",
        "//div[@role='dialog']//ul",
    ]
    for xpath in candidates:
        try:
            el = driver.find_element(By.XPATH, xpath)
            if el:
                return el
        except:
            continue
    
    return driver.find_element(By.XPATH, "//div[@role='dialog']")


def scroll_and_collect(driver, total_expected, list_type):
    """
    Scroll the modal list and collect usernames from _ap3a spans.
    Stops when collected >= total_expected OR no new names after several scrolls.
    """
    wait = WebDriverWait(driver, 15)

    
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
    human_sleep(1.5, 2)

    
    scroll_box = find_scroll_container(driver)

    users = set()
    stall_count = 0
    max_stalls = 8   
    scroll_pause = 2.0  

    print(f"  Scrolling to collect all {list_type} (expected ~{total_expected})...")

    while True:
        
        spans = driver.find_elements(By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade")
        prev_count = len(users)

        for span in spans:
            text = span.text.strip()
            if text and " " not in text:  
                users.add(text)

        print(f"  → Collected {len(users)}/{total_expected} {list_type}...", end="\r")

        
        if len(users) >= total_expected:
            break

        if len(users) == prev_count:
            stall_count += 1
            if stall_count >= max_stalls:
                print(f"\n No new names after {max_stalls} scrolls, stopping.")
                break
        else:
            stall_count = 0  

        
        try:
            driver.execute_script(
                "arguments[0].scrollTop += arguments[0].offsetHeight;",
                scroll_box
            )
        except:
            
            try:
                scroll_box = find_scroll_container(driver)
                driver.execute_script(
                    "arguments[0].scrollTop += arguments[0].offsetHeight;",
                    scroll_box
                )
            except:
                pass

        
        time.sleep(scroll_pause)

    print(f"\n Collected {len(users)} {list_type}.")
    return users


def get_count_from_profile(driver, username, list_type):
    try:
        go_to_profile(driver, username)
        wait = WebDriverWait(driver, 10)

        if list_type == "followers":
            el = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href,'/followers/')]//span[@title]")
            ))
            count_text = el.get_attribute("title") or el.text

        else:
            try:
                el = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@href,'/following/')]//span[@title]")
                ))
                count_text = el.get_attribute("title")

            except:
                el = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@href,'/following/')]//span//span")
                ))
                count_text = el.text

        return int(count_text.replace(",", ""))

    except Exception as e:
        print("Error reading count:", e)
        return 9999


def get_followers(driver, username):
    print("\n Opening Followers list...")
    total = get_count_from_profile(driver, username, "followers")

    go_to_profile(driver, username)
    wait = WebDriverWait(driver, 15)
    followers_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@href, '/followers/')]")
    ))
    followers_link.click()
    human_sleep(2, 3)

    users = scroll_and_collect(driver, total, "followers")
    return users


def get_following(driver, username):
    print("\n Opening Following list...")
    total = get_count_from_profile(driver, username, "following")

    go_to_profile(driver, username)
    wait = WebDriverWait(driver, 15)
    following_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@href, '/following/')]")
    ))
    following_link.click()
    human_sleep(2, 3)

    users = scroll_and_collect(driver, total, "following")
    return users


def close_modal(driver):
    try:
        close_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button._abl-")
        ))
        close_btn.click()
        human_sleep(1, 2)
    except:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            human_sleep(1, 2)
        except:
            pass


def print_report(non_followers, followers, following):
    print("\n" + "═" * 50)
    print("         INSTAGRAM REPORT")
    print("═" * 50)
    print(f"  You follow        : {len(following)}")
    print(f"  Follow you back   : {len(followers)}")
    print(f"  NOT following back: {len(non_followers)}")
    print("═" * 50)

    if non_followers:
        print("\n People NOT following you back:\n")
        for i, user in enumerate(sorted(non_followers), 1):
            print(f"  {i:3}. @{user}")
    else:
        print("\n Everyone you follow follows you back!")

    print("\n" + "═" * 50)


def main():
    global USERNAME, PASSWORD

    if not USERNAME:
        USERNAME = input(" Enter your Instagram username: ").strip()
    if not PASSWORD:
        PASSWORD = getpass.getpass(" Enter your Instagram password (hidden): ").strip()

    driver = init_driver(headless=HEADLESS)
    try:
        login(driver, USERNAME, PASSWORD)

        followers = get_followers(driver, USERNAME)
        close_modal(driver)

        following = get_following(driver, USERNAME)
        close_modal(driver)

        non_followers = following - followers
        print_report(non_followers, followers, following)

    except Exception as e:
        print(f"\n Error: {e}")
        raise
    finally:
        print("\n" + "─" * 50)
        input(" Press ENTER to close the browser and exit...")
        driver.quit()
        print(" Browser closed. ")


if __name__ == "__main__":
    main()
