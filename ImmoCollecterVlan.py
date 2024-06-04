from ImmoCollecterItf import ImmoCollecterItf
from ImmoCollecterTools import ImmoCollecterTools
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import json
import math
import datetime
import re

CONVERSION_TABLE = {
    'id': ['id'],
    'customerId': ['seller_id'],
    'customerType': ['seller_type'],
    'price_main': ['price'],
    'price_old': [],
    'price_type': [],
    'title': ['title'],
    'description': ['description'],
    'surface': ['livable_surface'],
    'bedrooms': [],
    'livingRoom': [],
    'condition': [],
    'constructionYear' : [],
    'landSurface': [],
    'postalcode': ['location','postalCode'],
    'city': ['location','addressLocality'],
    'street': ['location', 'streetAddress'],
    'number': [],
    'type': ['property_type'],
    'subtype': ['property_sub_type'],
    'creationDate': [],
    'expirationDate': [],
    'lastModificationDate': ['lastModificationDate'],
    'epcScore': [],
    'primaryEnergyConsumptionPerSqm': [],
    'bathrooms': [],
    'parking': [],
    'livingRoom': []
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


class ImmoVlan(ImmoCollecterItf):
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
        res = soup.find_all(string = re.compile("zoekertjes"))
        for el in res:
            spl = el.split(u'\xa0')
            if len(spl) > 1 and spl[1].lower() == "zoekertjes":
                total_houses = int(spl[0])
        if total_houses == -1:
            print("Error: No total announcements found. Please review the URL.")
        return total_houses

    def _get_total_pages(self, url):
        try:
            total_pages = math.ceil(self._get_total_houses(url)/20)
        except TypeError as err:
            print("Error: No search page found. Please review the URL")
            total_pages = -1
        return total_pages

    def get_list_all_houses(self) :
        total_pages = min(self._get_total_pages(self.search_url), 10)  # only go up to 6 pages
        houses = []

        # second options: STORAGE_KEY_SEARCH_RESULTS -> already json
        for page in range(1,total_pages+1):
            url = self.search_url + '&page='+str(page)
            search_page = self._request_url(url)
            
            soup = BeautifulSoup(search_page.text, "html.parser")
            house_list = soup.find_all("article", { "itemtype":"http://schema.org/SingleFamilyResidence"})
            
            for house in house_list:
                url = house["data-url"]
                id = url.split('/')[-1].lower().strip()
                if len(id) != 8:
                    print(f"Error, vlan id: {id} is not 8 characters long, parse error?")
                    continue
                houses.append({ 'id': f"vlan_{id}", 'url': url})
        return houses

    def get_house_details(self, house_ref):
        # Return a json with all data from a specific classified
        house_url = house_ref['url']
        print(house_url)
        house_page = self._request_url(house_url)
        soup = BeautifulSoup (house_page.text, "html.parser")
        scripts = soup.find_all("script", { "type": "application/ld+json" })
        house = {}
        for script in scripts:
            if "SellAction" in script.string:
                try:
                    house = json.loads(script.string)
                    break
                except Exception as e:
                    print(f'Error, vlan house ({house_ref["id"]}) could not be parsed: {str(e)}')
                    return house
        if not house:
            print(f'Error, vlan house: ({house_ref["id"]}) did not contain data structure to parse: {house_ref["url"]}')
            return house
        
        
        data_segment = soup.find(string = re.compile("livable_surface"))
        json_string = data_segment.string.split('(')[1].split(')')[0].split("||")[0]
        try:
            data = json.loads(json_string)
            house.update(data)
        except Exception as e:
            print(f'Error, vlan house ({house_ref["id"]}) 2nd data could not be parsed: {str(e)} \n {json_string}')
        
        house["id"] = house_ref["id"]
        house["title"] = soup.find("title").string
        mod_date = soup.find(string = re.compile("Laatste aanpassing"))
        mod_date_string = mod_date.string if mod_date else ''
        house['lastModificationDate'] = datetime.datetime.strptime(mod_date.split(' ')[-1], '%d/%m/%Y').strftime('%Y-%m-%dT12:00:00') if mod_date_string else datetime.datetime.now().strftime('%Y-%m-%dT12:00:00')
        
        normalized_house = ImmoCollecterTools.extract_data_house(house, CONVERSION_TABLE)
        normalized_house["url"] = house_url
        normalized_house['lastSeen'] = datetime.datetime.now()
        normalized_house["displayAd"] = 1
        normalized_house['immoProvider'] = "vlan"

        images = soup.find_all("a", {"class": "img-thumb"})
        image_urls = []
        for image in images:
            image_urls.append(image["data-src"])
        normalized_house['pictureUrls'] = ",".join(image_urls)
        normalized_house['pictureDownloads'] = image_urls
        
        return normalized_house

    @staticmethod
    def is_house_gone(url):
        try:
            house_page = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup (house_page.text, "html.parser")
            scripts = soup.find_all("script", { "type": "application/ld+json" })
            house = {}
            for script in scripts:
                if "SellAction" in script.string:
                    house = json.loads(script.string)
                    break
            if not house:
                return True
        except:
            return True
        return False


if __name__ == "__main__":
    #ImmoVlan.is_house_gone("https://immo.vlan.be/nl/detail/huis/te-koop/9340/lede/rbi81856")
    
    search = "https://immo.vlan.be/nl/vastgoed?transactiontypes=te-koop,in-openbare-verkoop&propertytypes=huis&provinces=oost-vlaanderen,west-vlaanderen&tags=hasgarden&mintotalsurface=1000&maxprice=750000&facades=4&noindex=1"
    immo = ImmoVlan(search)
    house = {'url': 'https://immovlan.be/nl/detail/villa/te-koop/9255/buggenhout/rbi75364', 'id': 'rbi75364'}
    house_details = immo.get_house_details(house)
    
    house_list = immo.get_list_all_houses()
    for house in house_list:
        house_details = immo.get_house_details(house)
        
    
