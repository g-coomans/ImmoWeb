#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sqlite3
import datetime
import time
import random
from ImmoCollecterImmoWeb import ImmoWeb
from ImmoCollecterVlan import ImmoVlan
from ImmoCollecterTools import ImmoCollecterTools


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
    
    def close(self):
        self.conn.close()
        self.conn = None
        print(f"Added {self.new_house_count} new houses!")


def wait_randomized_time():
    time.sleep(random.choice([MIN_WAINTING,MAX_WAINTING]))

def fetch_houses_and_update_db(immo, database):
    house_list = immo.get_list_all_houses()
    database_houses = database.get_id_entries()
    wait_randomized_time()
    for house in house_list:
        house_details = immo.get_house_details(house)
        if not house_details:
            continue
        if house["id"] not in database_houses:
            house_details['pictureDownloads'] = ImmoCollecterTools.download_pictures(house_details['pictureDownloads'], PIC_DOWNLOAD_DIR)
            database.create_entry([house_details])
        else:
            database.update_entry(house_details)
        wait_randomized_time()



if __name__ == "__main__":

    # immoweb_search_url = "https://www.immoweb.be/nl/zoeken?propertyTypes=HOUSE&postalCodes=BE-8790,BE-9031&transactionTypes=FOR_SALE&minFacadeCount=4&districts=DENDERMONDE,KORTRIJK,AALST,OUDENAARDE,TIELT&priceType=PRICE&minLandSurface=550&countries=BE&maxPrice=700000&maxFacadeCount=4&orderBy=newest"
    # immo_web = ImmoWeb(immoweb_search_url)
    # immo_web_db = HouseDb()
    # print("Starting ImmoWeb search")
    # fetch_houses_and_update_db(immo_web, immo_web_db)
    # immo_web_db.close()
    
    vlan_search_url = "https://immo.vlan.be/nl/vastgoed?transactiontypes=te-koop,in-openbare-verkoop&propertytypes=huis&provinces=oost-vlaanderen,west-vlaanderen&tags=hasgarden&mintotalsurface=1000&maxprice=750000&facades=4&noindex=1"
    immo_vlan = ImmoVlan(vlan_search_url)
    immo_vlan_db = HouseDb()
    print("Starting Immo Vlan search")
    fetch_houses_and_update_db(immo_vlan, immo_vlan_db)
    immo_vlan_db.close()


