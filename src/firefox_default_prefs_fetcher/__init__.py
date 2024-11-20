# Built-ins
from os import name, makedirs, getenv
from pathlib import Path
from argparse import ArgumentParser
# Project imports
from .get_default_preferences import main as get_default_preferences_main
from .get_firefox_geckodriver_versions import main as get_firefox_geckodriver_versions_main

DEFAULT_OUT_DIR = "out/"
DEFAULT_PROFILE_NAME = "firefox-default-prefs-fetcher"
DEFAULT_FIREFOX_DATA_DIR = Path.home().joinpath(".mozilla/firefox").absolute() if name != "nt" else Path(getenv("APPDATA") + "/Mozilla/Firefox/").resolve()

def cli():
    argparser = ArgumentParser()

    argparser.add_argument("--out-dir", "-od", "-d", default=DEFAULT_OUT_DIR)

    # This is how you have to do it https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_mutually_exclusive_group
    group_modes_outer = argparser.add_argument_group("Modes")
    group_modes_inner = group_modes_outer.add_mutually_exclusive_group()
    group_modes_inner.add_argument("--get-default-preferences", "-gdp", "--get-preferences", "-gp",  action="store_const", default=True, help=". Will be used unless another mode is selected")
    group_modes_inner.add_argument("--get-firefox-geckodriver-versions", "-gfgv", "--get-versions", "-gv", action="store_true", default=False, help="Fetch data about currently existing Firefox versions & their compatible geckodriver versions. If passed, --get-default-preferences will be disabled")


    group_get_default_preferences = argparser.add_argument_group("get_default_preferences")

    group_get_default_preferences.add_argument("--headless", action="store_true", default=False, help="")
    group_get_default_preferences.add_argument("--ci", action="store_true", default=False, help="Disable profile backup, as such not requiring a default profile to exist before running. Implies headless")
    group_get_default_preferences.add_argument("--browser-version", "-bv", default=None, help="(Experimental Selenium Manager) Which version of Firefox to use. Selenium will download it if it can't find it locally. Defaults to None, which will use your installed Firefox")
    group_get_default_preferences.add_argument("--firefox-data-dir", "--firefox-data", default=DEFAULT_FIREFOX_DATA_DIR, help=f"Path to Firefox data dir. Defaults to {DEFAULT_FIREFOX_DATA_DIR}")
    group_get_default_preferences.add_argument("--profile-name", default=DEFAULT_PROFILE_NAME)
    group_get_default_preferences.add_argument("--continue-if-version-mismatch", action="store_true", default=False)

    args = argparser.parse_args()

    makedirs(args.out_dir, exist_ok=True)

    # Modes
    if args.get_firefox_geckodriver_versions:
        get_firefox_geckodriver_versions_main(args)
    else:
        get_default_preferences_main(args)

