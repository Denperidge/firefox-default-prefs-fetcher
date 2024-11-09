from pathlib import Path
from configparser import ConfigParser
from shutil import copytree

from selenium import webdriver

FIREFOX_ROOT = Path.home().joinpath(".mozilla/firefox").absolute() if name != "nt" else Path(getenv("APPDATA") + "/Mozilla/Firefox/").resolve()
PROFILE_NAME = "firefox-default-prefs-fetcher"

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


def new_profile(src):
    dest = f"{Path(src).with_name(PROFILE_NAME)}"    
    copytree(src, dest, ignore=ignore_patterns("*lock"))






#default_profile_folder = _get_default_profile_folder()

#driver = webdriver.Firefox()

#driver.get("about:config")