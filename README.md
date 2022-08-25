# ImmoWeb

## Which purpose ?
This is a web crawler for the belgian real estate website Immoweb.be
At the moment it can be used to crawl *sales ads*. Renting ads are not tested (but should work).

**You have to ask the permission to Immoweb.be to crawl their website.** 
My project doesn't guarantee their approbation. Thank to notice it.

## How to use ?
It uses the following (basic) packages :
- requests
- BeautifulSoup
- json
- math

Before to go :
1. you need to modify *URL* variable to match your search criteria.
Go on Immoweb.be, make your search then copy/paste the URL to *URL* variable.
** Verify that there is no *page=1* in your URL**
2. requests object (ideally with a session and headers)
and now ... go !
- getAds retrieves all ads informations from a specific search page
- getAd retrive all information from a specific ad page.

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
- ~~clarify *price_first* and *price_old*~~
- ~~add my use for example~~
- adapt to renting ads
- re-work updateAd 
- url generator for your request
- replace *requests* module by *requests-html* (look like useless)
