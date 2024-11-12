from pathlib import Path
from configparser import ConfigParser
from os import name, makedirs, getenv
from platform import system
from sys import argv
from shutil import copytree, ignore_patterns, rmtree
from json import dumps, loads
from argparse import ArgumentParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

DEFAULT_OUT_DIR = "out/"
DEFAULT_PROFILE_NAME = "firefox-default-prefs-fetcher"
DEFAULT_FIREFOX_DATA_DIR = Path.home().joinpath(".mozilla/firefox").absolute() if name != "nt" else Path(getenv("APPDATA") + "/Mozilla/Firefox/").resolve()
DEFAULT_FIREFOX_PROFILE_PATH = DEFAULT_FIREFOX_DATA_DIR.joinpath(DEFAULT_PROFILE_NAME)




def write_file(filename, data, out_dir=True):
    if out_dir:
        filename = DEFAULT_OUT_DIR + filename
    with open(filename, "w", encoding="utf-8") as file:
        file.write(data)

# Copied from yokoffing/Betterfox/install.py. But also I wrote that and I'm writing this for that
def get_default_profile_folder():
    config_path = DEFAULT_FIREFOX_DATA_DIR.joinpath("profiles.ini")
    
    print(f"Reading {config_path}...")

    config_parser = ConfigParser(strict=False)
    config_parser.read(config_path)

    for section in config_parser.sections():
        if "Default" in config_parser[section]:
            if config_parser[section]["Default"] == "1":
                print("Default detected: " + section)
                return DEFAULT_FIREFOX_DATA_DIR.joinpath(config_parser[section]["Path"])


def create_new_profile():
    default_profile_folder = get_default_profile_folder()
    if DEFAULT_FIREFOX_PROFILE_PATH.exists():
        print(f"{DEFAULT_FIREFOX_PROFILE_PATH} already exists.")
        print(f"You can optionally overwrite it with the contents of {default_profile_folder}")
        if not input(f"Overwrite profile '{DEFAULT_PROFILE_NAME}' [N/y]?: ").lower().strip().startswith("y"):
            return    

    dest = str(Path(default_profile_folder).with_name(DEFAULT_PROFILE_NAME))
    rmtree(dest)
    copytree(default_profile_folder, dest, ignore=ignore_patterns("*lock"))


def create_prefix(platform, firefox_version):
    return f"{platform}-{firefox_version}-"

def main():
    argparser = ArgumentParser()
    argparser.add_argument("--ci", action="store_true", default=False, help="")
    argparser.add_argument("--browser-version", "-bv", default=None, help="")
    argparser.add_argument("-")

    driver = None
    makedirs(DEFAULT_OUT_DIR, exist_ok=True)
    options = webdriver.FirefoxOptions()

    options.add_argument("about:config")
    if not RUNNING_IN_CI:
        create_new_profile()
        options.profile = webdriver.FirefoxProfile(profile_directory=str(DEFAULT_FIREFOX_PROFILE_PATH))
    else:
        options.add_argument("--headless")

    default_preferences = []

    try:
        print("Starting driver...")
        driver = webdriver.Firefox(options)
        options.browser_version = 
        firefox_version = driver.capabilities["browserVersion"]  # Thanks to https://stackoverflow.com/a/58989044
        platform = system().lower()
        if platform == "":
            print("Couldn't determined platform!")
            exit(1)
        prefix = create_prefix(platform=platform, firefox_version=firefox_version)

        # Bypass warning screen if it pops up
        try:
            driver.find_element(By.ID, "warningButton").click()
            print("Bypassed default warning screen...")
        except NoSuchElementException:
            print("No warning screen detected, continuing...")

        # Show all preferences
        driver.find_element(By.ID, "show-all").click()
        print("Clicked #show-all")
        
        # Reset all changed values
        reset_buttons = driver.find_elements(By.CLASS_NAME, "button-reset")
        for button in reset_buttons:
            button.click()
        if len(reset_buttons) > 0:
            print("Clicked reset buttons")
        else:
            print("No reset buttons found, cintinuing...")
        
        
        # Note custom/no-default/deprecated values
        no_defaults_found = []
        delete_buttons = driver.find_elements(By.CLASS_NAME, "button-delete")
        for button in delete_buttons:
            key_container = button.find_element(By.XPATH, "..").find_element(By.XPATH, "..").find_element(By.CSS_SELECTOR, "[scope='row']")
            key_element = key_container.find_element(By.TAG_NAME, "span")
            no_defaults_found.append(key_element.text)
        print("Preferences with no defaults parsed")
        
        if not RUNNING_IN_CI:
            write_file(prefix + "no_defaults_found.json", dumps(no_defaults_found))
            print(f"Saved entries without default values to out/{prefix}no_defaults_found.json")


        pref_rows = driver.find_element(By.ID, "prefs").find_elements(By.TAG_NAME, "tr")
        for pref_row in pref_rows:
            key = pref_row.find_element(By.TAG_NAME, "th").text
            if key in no_defaults_found:
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

        print("Collected all preferences & their default values")
        
    except Exception as e:
        print(e)
    finally:
        if driver is not None:
            print("Closing Selenium driver...")
            driver.close()
            print("Driver closed")

        if len(default_preferences) > 0:
            write_file(prefix + "defaults.min.json", dumps(default_preferences))
            write_file(prefix + "defaults.json", dumps(default_preferences, indent=2))
            print(f"Saved preferences/defaults to out/{prefix}defaults.json & out/${prefix}defaults.min.json")
        else:
            print("No default preferences found, skipping write")
