from ImmoCollecterItf import ImmoCollecterItf
from ImmoCollecterTools import ImmoCollecterTools
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import json
import math
import datetime
import re
import time

CONVERSION_TABLE = {
    'id': ['code'],
    'customerId': ['zimmo_kantoor_id'],
    'price_main': ['prijs'],
    'title': ['title'],
    'surface': ['woonopp'],
    'condition': [],
    'constructionYear' : ['bouwjaar'],
    'landSurface': ['grondopp'],
    'postalcode': ['postcode'],
    'city': ['gemeente'],
    'street': ['address'],
    'number': [],
    'type': ['type'],
    'subtype': ['subtype'],
    'creationDate': [],
    'expirationDate': [],
    'epcScore': ['epc'],
    'primaryEnergyConsumptionPerSqm': ['energyWaarde'],
    'bathrooms': [],
    'parking': [],
    'livingRoom': []
}

# https://useragentstring.com/
# HEADERS = {
#     'Accept': '*/*',
#     'Host': 'www.zimmo.be',
#     'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9) Gecko/2008051206 Firefox/3.0'
# }
HEADERS = {
    'Host': 'www.zimmo.be',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'DNT': '1',
    'Sec-GPC': '1'
    }


class ImmoZimmo(ImmoCollecterItf):
    def __init__(self, search_url) -> None:
        self.conn = None
        self.search_url = search_url
        self._create_connection()

    def _create_connection(self, headers=HEADERS):
        self.conn = requests.Session()
        self.conn.headers = headers

    def _request_url(self, url):
        try:
            response = self.conn.get(url)
            response.raise_for_status()  # If the response was succesful, no Exception will be raised
        except HTTPError as http_err:
            print(f'HTTP error occured : {http_err}')
        except Exception as err:
            print(f'Other error occured : {err}')
        
        return response

    def _get_total_houses(self, url):
        total_houses = -1
        search_page = self._request_url(url)
        soup = BeautifulSoup(search_page.text, "html.parser")
        res = soup.find_all(string = re.compile("resultaten"))
        for el in res:
            amount = "".join(list(filter(str.isdigit, el)))
            if amount != "":
                return int(amount)
        if total_houses == -1:
            print("Error: No total announcements found. Please review the URL.")
        return total_houses

    def _get_total_pages(self, url):
        try:
            total_pages = math.ceil(self._get_total_houses(url)/21)
        except TypeError as err:
            print("Error: No search page found. Please review the URL")
            total_pages = -1
        return total_pages
    
    def get_list_all_houses(self):
        total_pages = min(self._get_total_pages(self.search_url), 10)  # only go up to 6 pages
        total_houses = []
        for page in range(1,total_pages+1):
            url = self.search_url + '&p='+str(page)
            search_page = self._request_url(url)
            soup = BeautifulSoup(search_page.text, "html.parser")
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "$(function () {" in script.string:
                    for line in script.string.splitlines():
                        if line.strip().startswith("properties: ["):
                            json_string = '{{ {} "a":"b" }}'.format(line.strip())
                            json_string = json_string.replace('properties', '"properties"')
                            houses = json.loads(json_string)
                            total_houses.extend(houses['properties'])
        return total_houses

    @staticmethod
    def parse_last_seen(text):
        number = int("".join(list(filter(str.isdigit, text))))
        date_now = datetime.datetime.now()
        if "uren" in text.lower():
            return date_now - datetime.timedelta(hours=number)
        if "dagen" in text.lower():
            return date_now - datetime.timedelta(days=number)
        if "weken" in text.lower():
            return date_now - datetime.timedelta(days=number*7)
        return date_now

    def get_house_details(self, house_ref):
        # Return a json with all data from a specific classified
        house_url = "https://www.zimmo.be{}".format(house_ref['url'])
        print(house_url)
        house = {}
        try:
            search_page = self._request_url(house_url)
        except:
            return None
        # soup = BeautifulSoup(search_page.content, "html.parser")
        soup = BeautifulSoup(search_page.content, "lxml")
        house = {}
        houde_data_started = False
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "$(function () {" in script.string:      
                for line in script.string.splitlines():
                    cleaned_line = line.strip()
                    cleaned_line = cleaned_line.replace("'",'"')
                    if len(cleaned_line) > 0 and cleaned_line[-1] == ',':
                        cleaned_line = cleaned_line[0:-1]
                    if houde_data_started and cleaned_line == "});":
                        break
                    elif houde_data_started:
                        if cleaned_line.startswith("search: {") or cleaned_line.startswith("transparency: {"):
                            continue
                        parts = cleaned_line.split(":")
                        if len(parts) > 1:
                            json_string = ":".join(parts[1:])
                            try:
                                house[parts[0]] = json.loads(json_string)
                            except:
                                pass
                        else:
                            continue
                    elif cleaned_line.startswith("property: {"):
                        houde_data_started = True
        

        normalized_house = ImmoCollecterTools.extract_data_house(house, CONVERSION_TABLE)
        normalized_house["url"] = house_url
        a = soup.find("p", {"class": "description-block"})
        b = soup.find("div", {"class": "stat-block last-update"})
        time.sleep(0.7)  # beautiful soup needs a bit of time
        if a:
            normalized_house["description"] = a.text.strip()
        else:
            normalized_house["description"] = ""
        if 'energyLabel' in house_ref:
            normalized_house["epcScore"] = house_ref["energyLabel"]
        else:
            normalized_house["epcScore"] = ""
        normalized_house['lastSeen'] = datetime.datetime.now()
        normalized_house["displayAd"] = 1
        normalized_house['immoProvider'] = "zimmo"
        
        if b:
            normalized_house['lastModificationDate'] = ImmoZimmo.parse_last_seen(b.text.strip()).strftime('%Y-%m-%dT12:00:00')
        else:
            normalized_house['lastModificationDate'] = datetime.datetime.fromtimestamp(int(house_ref['toegevoegd'])).strftime('%Y-%m-%dT12:00:00')
        image_urls = []
        if 'images' in house:
            for image_set in house['images']:
                image_urls.append(image_set["z-detail"])

        normalized_house['pictureUrls'] = ",".join(image_urls)
        normalized_house['pictureDownloads'] = image_urls
        
        return normalized_house

    @staticmethod
    def is_house_gone(url):
        try:
            house_page = requests.get(url)
            soup = BeautifulSoup (house_page.text, "html.parser")
            scripts = soup.find_all("script", { "type": "application/ld+json" })
            house = {}
            for script in scripts:
                if "SellAction" in script.string:
                    house = json.loads(script.string)
            if not house:
                return True
        except:
            return True
        return False


if __name__ == "__main__":
    zimmo_search = "https://www.zimmo.be/nl/zoeken/?search=eyJmaWx0ZXIiOnsic3RhdHVzIjp7ImluIjpbIkZPUl9TQUxFIiwiVEFLRV9PVkVSIl19LCJwcmljZSI6eyJyYW5nZSI6eyJtYXgiOjU2MDAwMH0sInVua25vd24iOnRydWV9LCJwbG90U3VyZmFjZSI6eyJyYW5nZSI6eyJtaW4iOjk5OX0sInVua25vd24iOnRydWV9LCJjYXRlZ29yeSI6eyJpbiI6WyJIT1VTRSIsIlBMT1QiLCJDT01NRVJDSUFMIl19LCJjb25zdHJ1Y3Rpb25UeXBlIjp7ImluIjpbIk9QRU4iXSwidW5rbm93biI6dHJ1ZX0sInBsYWNlSWQiOnsiaW4iOlsxMjAsMTI5LDE2NSwxNzIsMjIsMjI1LDI1OCwyNiwyNzcsMjkzLDMwMCwzMDgsMzE4LDMzNSwzNDAsMzQ0LDM1NCwzNzAsMzg2LDM5Niw0MDksNDM0LDQ0LDQ1MCw0NjcsNTA0LDUyNyw1MzEsNTM3LDUzOCw1NDUsNTQ4LDU1Nyw1NjEsNTYzLDU3Miw2OCw4MCw5OCw5OV19fX0%3D#gallery"
    zim = ImmoZimmo(zimmo_search)
    house_list = zim.get_list_all_houses()
    for house in house_list:
        house_details = zim.get_house_details(house)