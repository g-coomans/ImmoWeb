from ImmoCollecterItf import ImmoCollecterItf
from ImmoCollecterTools import ImmoCollecterTools
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import json
import math
import datetime

CONVERSION_TABLE = {'id': ['id'],
    'customerId': ['customers', 0, 'id'],
    'customerType': ['customers', 0, 'type'],
    'price_main': ['price', 'mainValue'],
    'price_old': ['price', 'oldValue'],
    'price_type': ['price', 'type'],
    'title': ['property', 'title'],
    'description': ['property', 'description'],
    'surface': ['property', 'netHabitableSurface'],
    'bedrooms': ['property', 'bedroomCount'],
    'livingRoom': ['property', 'livingRoom'],
    'condition': ['property', 'building', 'condition'],
    'constructionYear' : ['property', 'building', 'constructionYear'],
    'landSurface': ['property', 'land', 'surface'],
    'postalcode': ['property', 'location','postalCode'],
    'city': ['property', 'location','locality'],
    'street': ['property', 'location', 'street'],
    'number': ['property', 'location', 'number'],
    'type': ['property', 'type'],'subtype': ['property', 'subtype'],
    'creationDate': ['publication', 'creationDate'],
    'expirationDate': ['publication', 'expirationDate'],
    'lastModificationDate': ['publication', 'lastModificationDate'],
    'epcScore': ['transaction', 'certificates', 'epcScore'],
    'primaryEnergyConsumptionPerSqm': ['transaction', 'certificates', 'primaryEnergyConsumptionPerSqm'],
    'bathroomCount': ['property', 'bathroomCount'],
    'showerRoomCount': ['property', 'showerRoomCount'],
    'parkingCountIndoor': ['property', 'parkingCountIndoor'],
    'parkingCountOutdoor': ['property', 'parkingCountOutdoor'],
    'livingRoom': ['property', 'livingRoom', 'surface'],
    'url' : ['url'], 
    }

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'}

class ImmoWeb(ImmoCollecterItf):
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
        search_page = self._request_url(url)

        soup = BeautifulSoup(search_page.text, "html.parser")
        try:
            total_houses = json.loads(soup.find("iw-search")[":result-count"])
        except TypeError as Err:
            print("Error: No total announcements found. Please review the URL.")
            total_houses = -1
            
        return total_houses

    def _get_total_pages(self, url):
        try:
            total_pages = math.ceil(self._get_total_houses(url)/30)
        except TypeError as err:
            print("Error: No search page found. Please review the URL")
            total_pages = -1
            
        return total_pages

    def get_list_all_houses(self) :
        total_pages = min(self._get_total_pages(self.search_url),8)  # only go up to 5 pages
        houses = []
        
        for page in range(1,total_pages+1):
            url = self.search_url + '&page='+str(page)
            search_page = self._request_url(url)
            soup = BeautifulSoup(search_page.text, "html.parser")
            houses.extend(json.loads(soup.find("iw-search")[":results"]))
        
        return houses

    def get_house_details(self, house_ref):
        # Return a json with all data from a specific classified
        #URL_AD = "https://www.immoweb.be/fr/annonce/"
        URL_IMMO = "https://www.immoweb.be/nl/zoekertje/"
        house_url = URL_IMMO + str(house_ref['id'])
        print(house_url)
        house_page = self._request_url(house_url)
        soup = BeautifulSoup (house_page.text, "html.parser")
        try:
            house = json.loads(soup.find("div", "classified").find("script").string.split("window.classified = ")[1][:-10])
        except AttributeError as err:
            print(f'Ad not find (ad = {id})')
        except UnboundLocalError as err:
            print(f'Ad not find (ad = {id})')
        
        normalized_house = ImmoCollecterTools.extract_data_house(house, CONVERSION_TABLE)
        normalized_house['bathrooms'] = normalized_house['bathroomCount'] if normalized_house['bathroomCount'] is not None else 0 + normalized_house['showerRoomCount'] if normalized_house['showerRoomCount'] is not None else 0
        normalized_house['parking'] = normalized_house['parkingCountIndoor'] if normalized_house['parkingCountIndoor'] is not None else 0 + normalized_house['parkingCountOutdoor'] if normalized_house['parkingCountOutdoor'] is not None else 0
        [normalized_house.pop(key) for key in ['bathroomCount', 'showerRoomCount', 'parkingCountIndoor', 'parkingCountOutdoor']]
        normalized_house['lastModificationDate'] = normalized_house['lastModificationDate'].split('.')[0]  # only keep '2023-08-12T01:10:00' from '2023-08-12T01:10:00.657+0000'
        
        pic_list = []
        pic_download = []
        if "media" in house:
            if "pictures" in house["media"]:
                for pic_item in house["media"]["pictures"]:
                    pic_list.append(pic_item['largeUrl'])
                    pic_download.append(pic_item['largeUrl'])  # or use: smallUrl, mediumUrl
        normalized_house['pictureUrls'] = ",".join(pic_list)
        normalized_house['pictureDownloads'] = pic_download
        
        normalized_house["url"] = house_url
        normalized_house['lastSeen'] = datetime.datetime.now()
        normalized_house["displayAd"] = 1
        normalized_house['immoProvider'] = "immoweb"
        
        return normalized_house

    @staticmethod
    def is_house_gone(url):
        try:
            house_page = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup (house_page.text, "html.parser")
            house = json.loads(soup.find("div", "classified").find("script").string.split("window.classified = ")[1][:-10])
        except:
            return True
        return False

