from pathlib import Path
from configparser import ConfigParser
from os import name
from shutil import copytree, ignore_patterns, rmtree

from selenium import webdriver
from selenium.webdriver.common.by import By

FIREFOX_ROOT = Path.home().joinpath(".mozilla/firefox").absolute() if name != "nt" else Path(getenv("APPDATA") + "/Mozilla/Firefox/").resolve()
PROFILE_NAME = "firefox-default-prefs-fetcher"
PROFILE_PATH = FIREFOX_ROOT.joinpath(PROFILE_NAME)

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
    create_new_profile()
    options = webdriver.FirefoxOptions()
    options.profile = webdriver.FirefoxProfile(profile_directory=str(PROFILE_PATH))
    
    options.add_argument("about:config")
    print("Starting driver...")
    driver = webdriver.Firefox(options)

    print("Find")
    #driver.get("about:config")


    driver.find_element(By.ID, "show-all").click()
    


#default_profile_folder = _get_default_profile_folder()

#driver = webdriver.Firefox()

#driver.get("about:config")