#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sqlite3
import datetime
import time
import random
import immoweb
import os
import requests


urlBuy = "https://www.immoweb.be/nl/zoeken?propertyTypes=HOUSE&postalCodes=BE-8790,BE-9031&transactionTypes=FOR_SALE&minFacadeCount=4&districts=DENDERMONDE,KORTRIJK,AALST,OUDENAARDE,TIELT&priceType=PRICE&minLandSurface=550&countries=BE&maxPrice=700000&maxFacadeCount=4&orderBy=newest"

DATABASE = './immodb.sqlite'
PIC_DOWNLOAD_DIR = "./static/img_cache"
# Wainting time (in sec) between two requests to website
MIN_WAINTING = 5 # in sec
MAX_WAINTING = 10 # in sec

def connectDb(): 
    cursor = sqlite3.connect(DATABASE)
    cursor.execute('''CREATE TABLE IF NOT EXISTS ad(id INTEGER,
        customerId INTEGER, customerType TEXT, price_main INTEGER,
        price_old INTEGER, price_type TEXT, title TEXT, description TEXT, surface INTEGER,
        bedrooms INTEGER, bathrooms INTEGER, livingRoom INTEGER,
        parking INTEGER, condition TEXT, constructionYear TEXT,
        landSurface INTEGER, postalcode TEXT, city TEXT, street text, number INTEGER,
        type text, subtype TEXT, creationDate TEXT, expirationDate TEXT,
        lastModificationDate TEXT, epcScore TEXT, primaryEnergyConsumptionPerSqm ,
        lastSeen TIMESTAMP, url TEXT, pictureUrls TEXT, pictureDownloads TEXT, displayAd INTEGER 
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
        print(f"Failed to insert ad (id = {ads['id']}) - {error}")
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

def formatDateFromAd(date):
    date = date.replace("T"," ")
    date = date.split("+")[0]
    return date

def waitingTime():
    time.sleep(random.choice([MIN_WAINTING,MAX_WAINTING]))

def updateData(database, session, url):
    storedAds = [ad[0] for ad in getStoredAds(database)] # List all knowed id from database
    totalPages = immoweb.getTotalPages(session, url)
    
    for page in range(1,totalPages+1):
        print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} - Start Page : {page} of {totalPages}')
        ads = immoweb.getAds(session, url, page) # Get all ads from a list page
        waitingTime()

        toUpdate = []
        toCreate = []
        for ad in ads:
            # If a id is already know, update price and lastSeen
            # else create a new entry.
            if ad['id'] in storedAds:
                toUpdate.append((ad['price']['mainValue'], datetime.datetime.now(), ad['id']))
                storedAds.remove(ad['id'])
                waitingTime()
            else:
                ad_details = immoweb.extractDataAd(immoweb.getAd(session, ad['id']))
                ad_details['pictureDownloads'] = downloadPictures(ad_details['pictureDownloads'], PIC_DOWNLOAD_DIR)
                toCreate.append(ad_details)
                waitingTime()
        if toUpdate:
            updateAds(database,toUpdate)
        if toCreate:
            createAds(database,toCreate)

def downloadPictures(urls, dowmload_dir):
    if not os.path.exists(dowmload_dir):
        os.mkdir(dowmload_dir)
    local_urls = []
    for pic_url in urls:
        pic_file_name = pic_url.split('/')[-1].split('?')[0]
        local_pic_path = os.path.join(dowmload_dir, pic_file_name)
        local_urls.append(local_pic_path)
        if os.path.exists(local_pic_path):
            continue
        try:
            with requests.get(pic_url, stream=True) as r:
                if r.status_code != 200:
                    print(f"Error downloading pic: {pic_url} : {str(r)}")
                with open(local_pic_path, 'wb') as f:
                    f.write(r.content)
        except Exception as e:
            print(f"Error downloading pic: {pic_url} : {str(e)}")
    return ",".join(local_urls)


if __name__ == "__main__":
    print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} - Launched')
    print(urlBuy)
    
    currentSession = immoweb.createConnection() # Open a connection 

    dataBase = connectDb() # Connect to Database
    updateData(dataBase, currentSession, urlBuy)
    dataBase.close()

    currentSession.close()
    print(f'{datetime.datetime.now().strftime("%H:%M %d/%m/%Y")} - Finished')


