#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import requests
import sqlite3
import datetime
import time
import random
import immoweb


URL = "https://www.immoweb.be/fr/recherche/maison/a-vendre?countries=BE&districts=BRUSSELS&orderBy=newest"
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'}
DATABASE = '~/immoweb/db.sqlite'
# Wainting time (in sec) between two requests to website
MIN_WAINTING = 3 # in sec
MAX_WAINTING = 10 # in sec

def connectDb(): 
    cursor = sqlite3.connect(DATABASE)
    cursor.execute('''CREATE TABLE IF NOT EXISTS ad(id INTEGER,
        customerId INTEGER, customerType TEXT, price_main INTEGER,
        price_old INTEGER, price_type TEXT, description TEXT, surface INTEGER,
        bedrooms INTEGER, bathrooms INTEGER, livingRoom INTEGER,
        parking INTEGER, condition TEXT, constructionYear TEXT,
        landSurface INTEGER, postalcode TEXT, street text, number INTEGER,
        type text, subtype TEXT, creationDate TEXT, expirationDate TEXT,
        lastModificationDate TEXT, epcScore TEXT, primaryEnergyConsumptionPerSqm ,
        lastSeen TIMESTAMP
        )''')
    return cursor

def updateAd(database, adId):
    try:
        sql = f'''UPDATE ad SET lastSeen = "{datetime.datetime.now()}" WHERE id = {adId}'''
        cursor = database.cursor()
        cursor.execute(sql)
        database.commit()
    except sqlite3.Error as error:
        print(f'Failed to update ad (id = {adId}) \n{error}\n{sql}')
    finally:
        cursor.close()
        
def createAd(database, ad):
    ### Create a new row in database based on keys of ad list.
    try: 
        attrib_names = ", ".join(ad.keys())
        attrib_values = ", ".join("?" * len(ad.keys()))
        sql = f''' INSERT INTO ad({attrib_names}) VALUES ({attrib_values}) '''
        
        cursor = database.cursor()
        cursor.execute(sql, list(ad.values()))
        database.commit()
    except sqlite3.Error as error:
        print(f"Failed to insert ad (id = {ad['id']}) - {error}")
    finally :
        cursor.close()

def getAllIds(database):
    ### Retrieve all id in the database
    try:
        sql = f''' SELECT id FROM ad '''
        
        cursor = database.cursor()
        cursor.execute(sql)
        allIds = cursor.fetchall()
    except sqlite3.Error as error:
        print(f"Failed to retrieve all Id's - {error}")
    finally :
        cursor.close()
    return allIds

        
def createConnection(headers):
    conn = requests.Session()
    conn.headers = headers
    
    return conn

def formatDateFromAd(date):
    date = date.replace("T"," ")
    date = date.split("+")[0]
    return date


def waitingTime():
    time.sleep(random.choice([MIN_WAINTING,MAX_WAINTING]))

if __name__ == "__main__":
    print(f'{20*"x"}\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} - Launched \n{20*"x"}')
    
    currentSession = createConnection(HEADERS) # Open a connection 
    dataBase = connectDb() # Connect to Database
    allIds = [id[0] for id in getAllIds(dataBase)] # List all knowed id from database 
   
    totalPages = immoweb.getTotalPages(currentSession, URL)
    for page in range(1,totalPages+1):
        print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} - Start Page : {page} of {totalPages}')
        ads = immoweb.getAds(currentSession, URL, page) # Get all ads from a list page
    
        listAdsId = [ad['id'] for ad in ads] # Retrieve all id from Ads
        waitingTime()
    
        for adId in listAdsId:
            # If a id is already know, lastSeen field for this entry is updated
            # else create a new entry.
            if adId in allIds:
                updateAd(dataBase,adId)
            else:
                createAd(dataBase,immoweb.extractDataAd(immoweb.getAd(currentSession, adId)))
                waitingTime()

    dataBase.close()
    currentSession.close()
    print(f'{20*"x"}\n{datetime.datetime.now().strftime("%H:%M %d/%m/%Y")} - Finished \n{20*"x"}')
