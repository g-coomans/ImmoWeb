# ImmoWeb

## Which purpose ?
This is a web crawler for the belgian real estate website Immoweb.be

**You have to ask the permission to Immoweb.be to crawl their website.** 
My project doesn't guarantee their approbation. Thank to notice it.

## How to use ?
It uses the following (basic) packages :
- requests
- BeautifulSoup
- json
- math
- datetime

I add *saveAds.py* to show how to use the project

## Which datas ?
Each ad contains a lot of data.
I limit to a few number based on my personal use :
- customer's id
- customer's type (agency, private, notary)
- first, actual and type price
- description
- surface (land and living surface)
- rooms (bedrooms, livingroom, bathroom, parking)
- condition
- construction year
- addres
- epc score

*EXTRACTED_DATA* can be changed to extract your desired data from ads. 

## What's next ?
I'm open to new features.