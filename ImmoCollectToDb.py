#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from ImmoCollecterImmoWeb import ImmoWeb
from ImmoCollecterVlan import ImmoVlan
from ImmoCollecterTools import ImmoCollecterTools
from ImmoCollecterZimmo import ImmoZimmo
import sqlite3
import time
import random
import threading
import argparse
import sys
import datetime
import dateutil.relativedelta

DATABASE = './immodb.sqlite'
PIC_DOWNLOAD_DIR = "./static/img_cache"
# Wainting time (in sec) between two requests to website
MIN_WAINTING = 3 # in sec
MAX_WAINTING = 10 # in sec

class HouseDb:
    def __init__(self) -> None:
        self.conn = None
        self.new_house_count = 0
        self.connect_db()
    
    def connect_db(self):
        self.conn = sqlite3.connect(DATABASE)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('''CREATE TABLE IF NOT EXISTS ad(id INTEGER,
        customerId INTEGER, customerType TEXT, price_main INTEGER,
        price_old INTEGER, price_type TEXT, title TEXT, description TEXT, surface INTEGER,
        bedrooms INTEGER, bathrooms INTEGER, livingRoom INTEGER,
        parking INTEGER, condition TEXT, constructionYear TEXT,
        landSurface INTEGER, postalcode TEXT, city TEXT, street text, number INTEGER,
        type text, subtype TEXT, creationDate TEXT, expirationDate TEXT,
        lastModificationDate TEXT, epcScore TEXT, primaryEnergyConsumptionPerSqm ,
        lastSeen TIMESTAMP, url TEXT, pictureUrls TEXT, pictureDownloads TEXT, displayAd INTEGER, immoProvider TEXT 
        )''')

    def update_entry(self,ad):
        try:
            self.conn.execute('UPDATE ad SET price_main = ?, lastSeen = ?, lastModificationDate = ? WHERE id = ?;', (ad['price_main'], ad['lastSeen'], ad['lastModificationDate'], ad['id']))
            self.conn.commit()
            #print(f"Updated {len(ads)} houses!")
        except sqlite3.Error as error:
            print(f'Failed in sqlite (id = {ad["id"]}) \n{error}')

    def create_entry(self, ads):
        try:
            attrib_names = ", ".join(ads[0].keys())
            attrib_values = ", ".join("?" * len(ads[0].keys()))
            sql = f'INSERT INTO ad({attrib_names}) VALUES ({attrib_values})'
            
            cursor = self.conn.cursor()
            data = list(map(list, (ad.values() for ad in ads)))
            cursor.executemany(sql, data)
            self.conn.commit()
            self.new_house_count += len(ads)
        except sqlite3.Error as error:
            print(f"Failed to insert ad (id = {ads['id']}) - {error}")
        finally :
            cursor.close()

    def get_id_entries(self):
        ids = []
        try:
            ids = [x['id'] for x in self.conn.execute("SELECT id FROM ad ORDER BY lastModificationDate DESC").fetchall()]
        except sqlite3.Error as error:
            print(f"Failed to retrieve all stored ads - {error}")
        return ids
    
    def get_id_and_url_entries(self):
        houses = []
        try:
            houses = [ {'id':x['id'],'url':x['url'],'provider':x['immoProvider'],'date':x['lastModificationDate'],'displayAd':x['displayAd']} for x in self.conn.execute("SELECT id,url,immoProvider,lastModificationDate,displayAd FROM ad ORDER BY lastModificationDate DESC").fetchall()]
        except sqlite3.Error as error:
            print(f"Failed to retrieve all stored ads - {error}")
        return houses
    
    def hide_ads(self, ids):
        for id in ids:
            try:
                self.conn.execute('UPDATE ad SET displayAd = 0 WHERE id = ?', (id,))
                self.conn.commit()
            except sqlite3.Error as error:
                print(f'Failed in sqlite (id = {id}) \n{error}')
    
    def close(self):
        self.conn.close()
        self.conn = None
        print(f"Added {self.new_house_count} new houses!")


def wait_randomized_time():
    time.sleep(random.choice([MIN_WAINTING,MAX_WAINTING]))

def fetch_houses_and_update_db(immo):
    database = HouseDb()
    house_list = immo.get_list_all_houses()
    print(f"++ Checking {len(house_list)} houses on: {type(immo)}")
    database_houses = database.get_id_entries()
    wait_randomized_time()
    for house in house_list:
        house_details = immo.get_house_details(house)
        if not house_details:
            continue
        if house_details["id"] not in database_houses:
            house_details['pictureDownloads'] = ImmoCollecterTools.download_pictures(house_details['pictureDownloads'], PIC_DOWNLOAD_DIR)
            database.create_entry([house_details])
        else:
            database.update_entry(house_details)
        wait_randomized_time()
    print(f"++ Finihsing {type(immo)}")
    database.close()

    
def cleanup_old_houses():
    database = HouseDb()
    houses = database.get_id_and_url_entries()
    date_limit = datetime.datetime.now() - dateutil.relativedelta.relativedelta(months=1)
    ids_to_delete = []
    for house in houses:
      date = datetime.datetime.strptime(house['date'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
      if date < date_limit and house['displayAd'] == 1:
          if house['provider'] == "immoweb":
            if ImmoWeb.is_house_gone(house['url']):
              ids_to_delete.append(house['id'])
          elif house['provider'] == "vlan":
            if ImmoVlan.is_house_gone(house['url']):
              ids_to_delete.append(house['id'])
          if len(ids_to_delete) % 10 == 9:
            wait_randomized_time()
    database.hide_ads(ids_to_delete)
    database.close()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect houses and add to the database")
    parser.add_argument('--cleanup', action="store_true", help='Check if house is still present on immosite, if not remove')
    args = parser.parse_args()
    if args.cleanup:
       print("Cleaning up old houses")
       cleanup_old_houses()
       sys.exit(0)
       
    #immoweb_search_url = "https://www.immoweb.be/nl/zoeken?propertyTypes=HOUSE&postalCodes=BE-8790,BE-9031&transactionTypes=FOR_SALE&minFacadeCount=4&districts=DENDERMONDE,KORTRIJK,AALST,OUDENAARDE,TIELT&priceType=PRICE&minLandSurface=550&countries=BE&maxPrice=700000&maxFacadeCount=4&orderBy=newest"
    immoweb_search_url = "https://www.immoweb.be/nl/zoeken/huis/te-koop?countries=BE&districts=AALST,DENDERMONDE,HALLE_VILVOORDE,KORTRIJK,OUDENAARDE,TIELT&maxPrice=680000&minLandSurface=550&postalCodes=7750,7760,7860,7880,7890,7910,9772&minFacadeCount=4&page=1&orderBy=relevance"
    #immo_bedrijf = "https://www.immoweb.be/nl/zoekertje/industriele-gebouwen/te-koop/maarke-kerkem/9680/10751415"
    vlan_search_url = "https://immo.vlan.be/nl/vastgoed?transactiontypes=te-koop,in-openbare-verkoop&towns=7880-vloesberg&municipals=kluisbergen,celles,lessines,elzele&propertytypes=huis,bedrijfsvastgoed,grond&propertysubtypes=huis,villa,huis-gemengd-gebruik,fermette,bungalow,boerderij---hoeve,kantoor&provinces=oost-vlaanderen,west-vlaanderen&tags=hasgarden&mintotalsurface=1000&maxprice=750000&facades=4&noindex=1"
    #vlan_bedrijf = "https://immo.vlan.be/nl/vastgoed?transactiontypes=te-koop&propertytypes=bedrijfsvastgoed&provinces=oost-vlaanderen,west-vlaanderen&mintotalsurface=900&maxprice=700000&page=2"
    zimmo_search_url = "https://www.zimmo.be/nl/zoeken/?search=eyJmaWx0ZXIiOnsic3RhdHVzIjp7ImluIjpbIkZPUl9TQUxFIiwiVEFLRV9PVkVSIl19LCJwcmljZSI6eyJyYW5nZSI6eyJtYXgiOjU2MDAwMH0sInVua25vd24iOnRydWV9LCJwbG90U3VyZmFjZSI6eyJyYW5nZSI6eyJtaW4iOjk5OX0sInVua25vd24iOnRydWV9LCJjYXRlZ29yeSI6eyJpbiI6WyJIT1VTRSIsIlBMT1QiLCJDT01NRVJDSUFMIl19LCJjb25zdHJ1Y3Rpb25UeXBlIjp7ImluIjpbIk9QRU4iXSwidW5rbm93biI6dHJ1ZX0sInBsYWNlSWQiOnsiaW4iOlsxMjAsMTI5LDE2NSwxNzIsMjIsMjI1LDI1OCwyNiwyNzcsMjkzLDMwMCwzMDgsMzE4LDMzNSwzNDAsMzQ0LDM1NCwzNzAsMzg2LDM5Niw0MDksNDM0LDQ0LDQ1MCw0NjcsNTA0LDUyNyw1MzEsNTM3LDUzOCw1NDUsNTQ4LDU1Nyw1NjEsNTYzLDU3Miw2OCw4MCw5OCw5OV19fX0%3D"
    
    threads = []
    threads.append(threading.Thread(target=fetch_houses_and_update_db, args=(ImmoWeb(immoweb_search_url),)))
    #threads.append(threading.Thread(target=fetch_houses_and_update_db, args=(ImmoWeb(immo_bedrijf),)))
    threads.append(threading.Thread(target=fetch_houses_and_update_db, args=(ImmoVlan(vlan_search_url),)))
    #threads.append(threading.Thread(target=fetch_houses_and_update_db, args=(ImmoVlan(vlan_bedrijf),)))
    threads.append(threading.Thread(target=fetch_houses_and_update_db, args=(ImmoZimmo(zimmo_search_url),)))

    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()



