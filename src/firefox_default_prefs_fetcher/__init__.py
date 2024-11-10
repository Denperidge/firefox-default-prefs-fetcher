from pathlib import Path
from configparser import ConfigParser
from os import name, makedirs
from shutil import copytree, ignore_patterns, rmtree
from json import dumps, loads

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

OUT_DIR = "out/"
FIREFOX_ROOT = Path.home().joinpath(".mozilla/firefox").absolute() if name != "nt" else Path(getenv("APPDATA") + "/Mozilla/Firefox/").resolve()
PROFILE_NAME = "firefox-default-prefs-fetcher"
PROFILE_PATH = FIREFOX_ROOT.joinpath(PROFILE_NAME)


def write_file(filename, data, out_dir=True):
    if out_dir:
        filename = OUT_DIR + filename
    with open(filename, "w", encoding="utf-8") as file:
        file.write(data)

# Copied from yokoffing/Betterfox/install.py. But also I wrote that and I'm writing this for that
def get_default_profile_folder():
    config_path = FIREFOX_ROOT.joinpath("profiles.ini")
    
    print(f"Reading {config_path}...")

    config_parser = ConfigParser(strict=False)
    config_parser.read(config_path)

    for section in config_parser.sections():
        if "Default" in config_parser[section]:
            if config_parser[section]["Default"] == "1":
                print("Default detected: " + section)
                return FIREFOX_ROOT.joinpath(config_parser[section]["Path"])


def create_new_profile():
    default_profile_folder = get_default_profile_folder()
    if PROFILE_PATH.exists():
        print(f"{PROFILE_PATH} already exists.")
        print(f"You can optionally overwrite it with the contents of {default_profile_folder}")
        if not input(f"Overwrite profile '{PROFILE_NAME}' [N/y]?: ").lower().strip().startswith("y"):
            return    

    dest = str(Path(default_profile_folder).with_name(PROFILE_NAME))
    rmtree(dest)
    copytree(default_profile_folder, dest, ignore=ignore_patterns("*lock"))


def main():
    makedirs(OUT_DIR, exist_ok=True)
    create_new_profile()
    options = webdriver.FirefoxOptions()
    options.profile = webdriver.FirefoxProfile(profile_directory=str(PROFILE_PATH))
    
    options.add_argument("about:config")
    print("Starting driver...")
    try:
        driver = webdriver.Firefox(options)

        print("Find")
        #driver.get("about:config")


        # Show all preferences
        driver.find_element(By.ID, "show-all").click()
        
        # Reset all changed values
        reset_buttons = driver.find_elements(By.CLASS_NAME, "button-reset")
        for button in reset_buttons:
            button.click()
        
        
        # Note custom/no-default/deprecated values
        no_defaults = []
        delete_buttons = driver.find_elements(By.CLASS_NAME, "button-delete")
        for button in delete_buttons:
            key_container = button.find_element(By.XPATH, "..").find_element(By.XPATH, "..").find_element(By.CSS_SELECTOR, "[scope='row']")
            key_element = key_container.find_element(By.TAG_NAME, "span")
            no_defaults.append(key_element.text)
        
        write_file("no_defaults.json", dumps(no_defaults))

        default_preferences = []

        pref_rows = driver.find_element(By.ID, "prefs").find_elements(By.TAG_NAME, "tr")
        for pref_row in pref_rows:
            key = pref_row.find_element(By.TAG_NAME, "th").text
            if key in no_defaults:
                continue
            try:
                # If this element doesn't throw NoSuchElement, it's a custom value that slipped through
                pref_row.find_element(By.CLASS_NAME, "button-delete")
                continue
            except NoSuchElementException as e:
                pass

            # This returns a json string with {value: ""}
            pref = pref_row.find_element(By.CSS_SELECTOR, ".cell-value span").get_attribute("data-l10n-args")
            if pref is None:
                print(key, "has no default value, but wasn't found in no_defaults")
                continue
            
            pref = loads(pref)
            pref["key"] = key
            default_preferences.append(pref)
        
        write_file("defaults.min.json", dumps(default_preferences))
        write_file("defaults.json", dumps(default_preferences, indent=2))
    except Exception as e:
        print(e)
    finally:
        driver.close()
