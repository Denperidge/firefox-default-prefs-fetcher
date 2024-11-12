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


def create_new_profile(firefox_data_dir=DEFAULT_FIREFOX_DATA_DIR, new_firefox_profile_name=DEFAULT_PROFILE_NAME):
    new_firefox_profile_path = Path(firefox_data_dir).joinpath(new_firefox_profile_name)
    default_profile_folder = get_default_profile_folder()

    # If new profile already exists 
    if new_firefox_profile_path.exists():
        print(f"{new_firefox_profile_path} already exists.")
        print(f"You can optionally overwrite it with the contents of {default_profile_folder}")
        # Allow a (default) option to skip creating the new profile
        if not input(f"Overwrite profile '{new_firefox_profile_name}' [N/y]?: ").lower().strip().startswith("y"):
            return new_firefox_profile_path
        else:
            pass  # Clarity
    
    # Remove new profile if it exists
    rmtree(new_firefox_profile_path)
    # Copy default profile folder to new profile path
    copytree(default_profile_folder, dest, ignore=ignore_patterns("*lock"))
    return new_firefox_profile_path

def create_prefix(platform, firefox_version):
    return f"{platform}-{firefox_version}-"

def main():
    argparser = ArgumentParser()
    argparser.add_argument("--headless", action="store_true", default=False, help="")
    argparser.add_argument("--ci", action="store_true", default=False, help="Disable profile backup, as such not requiring a default profile to exist before running. Implies headless")
    argparser.add_argument("--browser-version", "-bv", default=None, help="Which version of Firefox to use. Selenium will download it if it can't find it locally. Defaults to None, which will use your installed Firefox")
    argparser.add_argument("--firefox-data-dir", "--firefox-data", default=DEFAULT_FIREFOX_DATA_DIR, help=f"Path to Firefox data dir. Defaults to {DEFAULT_FIREFOX_DATA_DIR}")
    argparser.add_argument("--profile-name", default=DEFAULT_PROFILE_NAME)
    argparser.add_argument("--continue-if-version-mismatch", action="store_true", default=False)

    platform = system().lower()
    if platform == "":
        print("Couldn't determined platform!")
        exit(1)

    args = argparser.parse_args()
    if args.ci:
        args.headless = True
        #args.force_downloads = True

    driver = None
    makedirs(DEFAULT_OUT_DIR, exist_ok=True)
    options = webdriver.FirefoxOptions()

    options.add_argument("about:config")
    if not args.ci:
        new_profile = create_new_profile(args.firefox_data_dir, args.profile_name)
        options.profile = webdriver.FirefoxProfile(profile_directory=str(new_profile))
    
    if args.browser_version:
        options.browser_version = args.browser_version
        print(f"Browser version selected: '{options.browser_version}'")

    
    if args.headless:
        options.add_argument("--headless")
    

    default_preferences = []

    try:
        print("Starting driver...")
        driver = webdriver.Firefox(options)

        detected_browser_version = driver.capabilities["browserVersion"]  # Thanks to https://stackoverflow.com/a/58989044
        prefix = create_prefix(platform=platform, firefox_version=detected_browser_version)
        print(f"Detected browser version: '{detected_browser_version}'")

        if args.browser_version:
            try:
                assert detected_browser_version == args.browser_version
            except AssertionError as e:
                if args.continue_if_version_mismatch:
                    print("--continue-on-version-mismatch specified, continuing...")
                else:
                    raise e
                

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
        
        if not running_in_ci:
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
