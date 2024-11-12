from urllib.request import urlopen
from io import BytesIO
from json import dumps
from re import compile, MULTILINE

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


def get_firefox_versions():
    hrefs = pq(url="https://ftp.mozilla.org/pub/firefox/releases/").find("table a")
    versions = set()
    for href in hrefs:
        version = pq(href).text()
        if REGEX_MATCH_SEMANTIC_VERSIONING.match(version) is not None:
            versions.add(version.replace("/", ""))
    
    versions = list(versions)
    # from https://stackoverflow.com/a/2574090
    versions.sort(reverse=True, key=lambda v: [int(n) for n in v.replace("esr", "").split(".")])

    print(versions)        
    



def get_versions_main():
    get_geckodriver_versions()
    get_firefox_versions()