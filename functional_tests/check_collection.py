import json
import sys
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

try:
    COLLECTION_CONFIG_FOLDER = sys.argv[1]
except IndexError:
    print("Please provide the collection config folder as an argument.")
    sys.exit(1)


def server_url(config_folder, server="test", secret=True) -> str:
    URLS = {
        "test": "https://sciencediscoveryengine.test.nasa.gov",
        "prod": "https://sciencediscoveryengine.nasa.gov",
    }
    if secret:
        query = "query-sde-primary"
        app = "nasa-sba-sde"
        folder = "SDE"
    else:
        query = "query-smd-primary"
        app = "nasa-sba-smd"
        folder = "SMD"

    base_url = URLS[server]
    payload = {
        "name": query,
        "scope": "All",
        "text": "",
        "advanced": {
            "collection": f"/{folder}/{config_folder}/",
        },
    }
    encoded_payload = urllib.parse.quote(json.dumps(payload))
    return f"{base_url}/app/{app}/#/search?query={encoded_payload}"


# Set up the Chrome WebDriver
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()

# Initialize the browser
driver = webdriver.Chrome(service=service, options=options)

first = True
n = 0
for server in ["test", "prod"]:
    for secret in [True, False]:
        if not first:
            n += 1
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[n])
        driver.get(server_url(COLLECTION_CONFIG_FOLDER, server=server, secret=secret))
        time.sleep(1)
        new_title = f"{'Secret' if secret else 'Regular'}{server.title()}"
        driver.execute_script("document.title = arguments[0]", new_title)
        first = False
        break
    break
driver.switch_to.window(driver.window_handles[0])

# Keep the browser open indefinitely
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting the script...")

# Close the browser after some time or interaction
driver.quit()
