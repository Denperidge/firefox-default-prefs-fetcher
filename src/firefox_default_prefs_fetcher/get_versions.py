from urllib.request import urlopen
from io import BytesIO
from json import dumps
from re import compile, MULTILINE
from yaml import dump as dump_yaml

from pyquery import PyQuery as pq

from .get_preferences import DEFAULT_OUT_DIR, write_file

REGEX_MATCH_SEMANTIC_VERSIONING = compile(r"^\d*\.\d*(\.\d*)?(esr)?/", MULTILINE)

class GeckodriverVersion():
    def __init__(self, geckodriver_version, min_firefox_version, max_firefox_version):
        self.geckodriver_version = geckodriver_version
        self.min_firefox_version = min_firefox_version
        if max_firefox_version == "n/a":
            self.max_firefox_version = max_firefox_version

def get_text_from_element(element, remove_spaces=False):
    text = pq(element).text()
    if not remove_spaces:
        return text
    else:
        return text.replace(" ", "")

def get_data(url):
    return urlopen(url)
    #return data

def get_geckodriver_versions():
    geckodriver_page = pq(url="https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html")
    
    geckodriver_versions = []

    skip_rows = 2
    rows = geckodriver_page.find("#supported-platforms table tr")
    for row in rows:  
        if skip_rows > 0:
            skip_rows -= 1
            continue
   
        columns = pq(row).find("td")

        if len(columns) <= 0:
            continue

        geckodriver_version = dict()

        geckodriver_version["geckodriver_version"] = get_text_from_element(columns[0], True)
        geckodriver_version["min_firefox_version"] = get_text_from_element(columns[2], True)
        max_firefox_version = get_text_from_element(columns[3], True)
        if max_firefox_version != "n/a":
            geckodriver_version["max_firefox_version"] = max_firefox_version
        
        geckodriver_versions.append(geckodriver_version)


    #print(geckodriver_versions)
        
    write_file("geckodriver_versions.json", dumps(geckodriver_versions, indent=2))
    write_file("geckodriver_versions.min.json", dumps(geckodriver_versions))
    
    return geckodriver_versions


def get_firefox_versions():
    hrefs = pq(url="https://ftp.mozilla.org/pub/firefox/releases/").find("table a")
    firefox_versions = set()
    for href in hrefs:
        version = pq(href).text()
        if REGEX_MATCH_SEMANTIC_VERSIONING.match(version) is not None:
            firefox_versions.add(version.replace("/", ""))
    
    firefox_versions = list(firefox_versions)
    # from https://stackoverflow.com/a/2574090
    firefox_versions.sort(reverse=True, key=lambda v: [int(n) for n in v.replace("esr", "").split(".")])

    write_file("firefox_versions.json", dumps(firefox_versions, indent=2))
    write_file("firefox_versions.min.json", dumps(firefox_versions))
    
    return firefox_versions

def get_major_version(version):
    return int(version.split(".")[0])

def get_versions_main():

    # These are both sorted from newest to oldest
    geckodriver_versions = get_geckodriver_versions()
    firefox_versions = get_firefox_versions()
    firefox_newest_geckodriver = {}

    for firefox_version in firefox_versions:
        print()
        print(f"--- Searching highest compatible Geckodriver for {firefox_version}---")
        for geckodriver_version_data in geckodriver_versions:
            geckodriver_version = geckodriver_version_data["geckodriver_version"]
            # These values are major versions (e.g. 132, 10.0.4esr)
            # The only available versions of these should be the ESR releases, as such it isn't relevant here

            major_firefox_version = get_major_version(firefox_version)
            min_major_firefox_version = int(geckodriver_version_data["min_firefox_version"].replace("ESR", ""))
            max_major_firefox_version = None
            if "max_firefox_version" in geckodriver_version_data.keys():
                max_major_firefox_version = int(geckodriver_version_data["max_firefox_version"].replace("ESR", ""))
                
            
            if major_firefox_version >= min_major_firefox_version:
                print(f"geckodriver {geckodriver_version}: {firefox_version} is above minimum ({min_major_firefox_version})...")
                
                if max_major_firefox_version is None:
                    print("... and has no maximum version!")
                    firefox_newest_geckodriver[firefox_version] = geckodriver_version
                    break
                else:
                    if major_firefox_version <= max_major_firefox_version:
                        print(f"... and is under or equal to the maximum version ({max_major_firefox_version})")
                        firefox_newest_geckodriver[firefox_version] = geckodriver_version
                        break
                    else:
                        print(f"... and is over the maximum version ({max_major_firefox_version})")
            else:
                print(f"geckodriver {geckodriver_version}: {firefox_version} is below minimum ({min_major_firefox_version}). Skipping.")
                continue
    
    actions_firefox_array = []
    for firefox_version in firefox_newest_geckodriver:
        data = {}
        data["firefox"] = firefox_version
        data["geckodriver"] = geckodriver_version
        actions_firefox_array.append(data)
    write_file("firefox_newest_geckodriver.min.json", dumps(firefox_newest_geckodriver))
    write_file("firefox_newest_geckodriver.json", dumps(firefox_newest_geckodriver, indent=2))
        
    write_file("firefox-matrix.yaml", dump_yaml(actions_firefox_array))
    #with open(DEFAULT_OUT_DIR + "firefox-matrix.yaml", "w", encoding="UTF-8") as file:

