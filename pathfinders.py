from requests import get 
from bs4 import BeautifulSoup 
import re
import urllib.request
import csv 

#this script was created to gather all of the potential applications links that are used within the NASA Data Pathfinders 
#resource i used for help: https://www.dataquest.io/blog/web-scraping-beautifulsoup/ 

#list of all of the NASA Data Pathfinders 
pathfinders_list = ['https://earthdata.nasa.gov/learn/pathfinders/sea-level-change', 'https://earthdata.nasa.gov/learn/pathfinders/wildfire-data-pathfinder', 
'https://earthdata.nasa.gov/learn/pathfinders/agricultural-and-water-resources-data-pathfinder', 'https://earthdata.nasa.gov/learn/pathfinders/biodiversity',
'https://earthdata.nasa.gov/learn/pathfinders/covid-19', 'https://earthdata.nasa.gov/learn/pathfinders/disasters', 'https://earthdata.nasa.gov/learn/pathfinders/gis-pathfinder',
'https://earthdata.nasa.gov/learn/pathfinders/health-and-air-quality-data-pathfinder', 'https://earthdata.nasa.gov/learn/pathfinders/water-quality-data-pathfinder']

data = {}

for pathfinder in pathfinders_list:
    #print(pathfinder)
    urls = []
    webs = ""
    moreWebs = ""
    response = get(pathfinder)
    html_soup = BeautifulSoup(response.text, 'html.parser')

    pathfinder_containers = html_soup.find_all('div',class_='eui-accordion is-closed')
    pathfinder_title = html_soup.find('h1').get_text().split('Data Pathfinder')
    #print(pathfinder_title[0])

    #go through all of the tabs in the pathfinder, until it's one of these: 
    #'other NASA assets of interests', 'external resources', 'other resources'
    for container in pathfinder_containers:
        if html_soup.find('h2') != None:
            if 'Assets' is container.h2.text:
                print(container)
                webs = container.findAll('a', attrs={'href': re.compile("^http")})
            elif 'Resources' in container.h2.text:
                moreWebs = container.findAll('a', attrs={'href': re.compile("^http")})
        else:
            #certain pathfinders reference the title of the container either in h2 OR h3 
            if 'Assets' is container.h3.text:
                print(container)
                webs = container.findAll('a', attrs={'href': re.compile("^http")})
            elif 'Resources' in container.h3.text:
                moreWebs = container.findAll('a', attrs={'href': re.compile("^http")})

    for website in webs:
        url = website['href']
        urls.append(url)

    for website in moreWebs:
        url = website['href']
        urls.append(url)
    
    for url in urls:
        #certain files we don't need, but can be scraped unintentially with https://
        if "jpg" in url:
            urls.remove(url)
        elif "youtube" in url:
            urls.remove(url)
        elif "photo" in url:
            urls.remove(url)

    #adds to the dictionary based on the Pathfinder title 
    data[pathfinder_title[0]] = urls 

#print(data)

#writes all urls to a CSV file - avoided Pandas since it was hard to export in the desireable format within CSV 
with open("PathfindersOutput.csv", "w") as csvfile:
    csv_fields = ['Pathfinder Topic', 'Potential Application Link']
    writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
    writer.writeheader()
    for key, urls in data.items():
        for url in urls: 
            writer.writerow({'Pathfinder Topic':key, 'Potential Application Link':url})
