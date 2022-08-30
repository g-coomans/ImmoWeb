#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import requests
import sqlite3
import datetime
import time
import random
import immoweb


urlRent = "https://www.immoweb.be/fr/recherche/maison-et-appartement/a-louer/brussels/arrondissement?countries=BE&page=1&orderBy=newest"
urlBuy = "https://www.immoweb.be/fr/recherche/maison-et-appartement/a-vendre/bruxelles/arrondissement?countries=BE&page=1&orderBy=newest"
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'}
DATABASE = '/home/geoffrey/ImmoWeb/db.sqlite'
# Wainting time (in sec) between two requests to website
MIN_WAINTING = 5 # in sec
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

def updateAds(database,ads):
    try:
        sql = '''UPDATE ad SET price_main = ?, lastSeen=? WHERE id = ?;'''
        cursor = database.cursor()
        cursor.executemany(sql, ads)
        database.commit()
    except sqlite3.Error as error:
        print(f'Failed in sqlite (id = {ads}) \n{error}\n{sql}')
    finally:
        cursor.close()    

def createAds(database, ads):
    ### Create new rows in database based on keys of ad list.
    try:
        attrib_names = ", ".join(ads[0].keys())
        attrib_values = ", ".join("?" * len(ads[0].keys()))
        sql = f''' INSERT INTO ad({attrib_names}) VALUES ({attrib_values}) '''
        
        cursor = database.cursor()
        data = list(map(list, (ad.values() for ad in ads)))
        cursor.executemany(sql, data)
        database.commit()
    except sqlite3.Error as error:
        print(f"Failed to insert ad (id = {ad['id']}) - {error}")
    finally :
        cursor.close()

def getStoredAds(database):
    ### Retrieve all id in the database
    try:
        sql = f''' SELECT id FROM ad '''
        
        cursor = database.cursor()
        cursor.execute(sql)
        allIds = cursor.fetchall()
    except sqlite3.Error as error:
        print(f"Failed to retrieve all stored ads - {error}")
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

def updateData(database, session, url):
    storedAds = [ad[0] for ad in getStoredAds(dataBase)] # List all knowed id from database
    totalPages = immoweb.getTotalPages(currentSession, url)
    
    for page in range(1,totalPages+1):
        print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} - Start Page : {page} of {totalPages}')
        ads = immoweb.getAds(currentSession, url, page) # Get all ads from a list page
        waitingTime()

        toUpdate = []
        toCreate = []
        for ad in ads:
            # If a id is already know, update price and lastSeen
            # else create a new entry.
            if ad['id'] in storedAds:
                toUpdate.append((ad['price']['mainValue'], datetime.datetime.now(), ad['id']))
                storedAds.remove(ad['id'])
            else:
                toCreate.append(immoweb.extractDataAd(immoweb.getAd(currentSession, ad['id'])))
                waitingTime()
        if toUpdate:
            updateAds(dataBase,toUpdate)
        if toCreate:
            createAds(dataBase,toCreate)


if __name__ == "__main__":
    print(f'{20*"x"}\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} - Launched \n{20*"x"}')
    
    currentSession = createConnection(HEADERS) # Open a connection 
    dataBase = connectDb() # Connect to Database

    updateData(dataBase, currentSession, urlBuy)
    updateData(dataBase, currentSession, urlRent)

    dataBase.close()
    currentSession.close()
    print(f'{20*"x"}\n{datetime.datetime.now().strftime("%H:%M %d/%m/%Y")} - Finished \n{20*"x"}')


