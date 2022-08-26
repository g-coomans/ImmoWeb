import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import json
import math

EXTRACTED_DATA = {'id': ['id'],
    'customerId': ['customers', 0, 'id'],
    'customerType': ['customers', 0, 'type'],
    'price_main': ['price', 'mainValue'],
    'price_old': ['price', 'oldValue'],
    'price_type': ['price', 'type'],
    'description': ['property', 'description'],
    'surface': ['property', 'netHabitableSurface'],
    'bedrooms': ['property', 'bedroomCount'],
    'livingRoom': ['property', 'livingRoom'],
    'condition': ['property', 'building', 'condition'],
    'constructionYear' : ['property', 'building', 'constructionYear'],
    'landSurface': ['property', 'land', 'surface'],
    'postalcode': ['property', 'location','postalCode'],
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
    'livingRoom': ['property', 'livingRoom', 'surface']
    }

def requestURL(conn, url):
    # Request page from url
    try:
        response = conn.get(url)
        
        # If the response was succesful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occured : {http_err}')
    except Exception as err:
        print(f'Other error occured : {err}')
    
    return response

def getTotalAds(conn, url):
    # return number of total ads for a search url
    adsPage = requestURL(conn, url)

    soup = BeautifulSoup(adsPage.text, "html.parser")
    try:
        totalAds = json.loads(soup.find("iw-search")[":result-count"])
    except TypeError as Err:
        print("No search page found. Please review the URL (getTotalAds)")
        totalAds = -1
        
    return totalAds

def getTotalPages(conn, url):
    # return number of result pages for a search url
    try:
        totalPages = math.ceil(getTotalAds(conn, url)/30)
    except TypeError as Err:
        print("No search page found. Please review the URL (getTotalAds)")
        totalPages = -1
        
    return totalPages

def getAds(conn, url, page) :
    # Return a json with all ads from a research page
    url = url + '&page='+str(page)
    adsPage = requestURL(conn, url)
    
    soup = BeautifulSoup(adsPage.text, "html.parser")
    ads = json.loads(soup.find("iw-search")[":results"])
    
    return ads

def getAd(conn, id):
    # Return a json with all data from a specific classified
    URL_AD = "https://www.immoweb.be/en/classified/"
    
    adPage = requestURL(conn, URL_AD + str(id))
    soup = BeautifulSoup (adPage.text, "html.parser")
    ad = json.loads(soup.find("div", "classified").find("script").string.split("window.classified = ")[1][:-10])
    
    
    return ad

def getDataFromTree(searchKey, data):
    # Extract data following the search Key in the list 'searchKey' in 'data' tree
    # can navigate in list or in dictionnary
    # example :
    # searchKey = ['price', 'mainValue']
    # data = ['price' : ['mainValue' : 500, 'lastValue' : 150], 'date' : 01/01/2022]
    # getDataFromTree returns 500
    try:
        if len(searchKey) > 1:
            if isinstance(searchKey[0], int):
                return getDataFromTree(searchKey[1:], data[0])
            elif isinstance(searchKey[0], str):
                return getDataFromTree(searchKey[1:], data.get(searchKey[0], None))
        elif len(searchKey) == 1 :
            if isinstance(searchKey[0], int):
                return data[searchKey[0]]
            elif isinstance(searchKey[0],str):
                return data.get(searchKey[0], None)
    except (TypeError, AttributeError) as error:
        print(f'Can\'t extract {searchKey}')
        return None

def extractDataAd(ad):
    # return all important information from a brut Json data classified based on EXTRACED_DATA variable
    dataAd = {}
    for key, value in EXTRACTED_DATA.items():
        dataAd[key] = getDataFromTree(value, ad)
    
    dataAd['bathrooms'] = dataAd['bathroomCount'] if dataAd['bathroomCount'] is not None else 0
    + dataAd['showerRoomCount'] if dataAd['showerRoomCount'] is not None else 0
    dataAd['parking'] = dataAd['parkingCountIndoor'] if dataAd['parkingCountIndoor'] is not None else 0
    + dataAd['parkingCountOutdoor'] if dataAd['parkingCountOutdoor'] is not None else 0
    
    removeKey = ['bathroomCount', 'showerRoomCount', 'parkingCountIndoor', 'parkingCountOutdoor']
    [dataAd.pop(key) for key in removeKey]
    
    return dataAd



   
