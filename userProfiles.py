import requests 
from bs4 import BeautifulSoup
import re
import pandas as pd 

#this script was written to extract potential application links and datasets referenced within NASA Data User Profiles 

#insert links to Data User Profiles within urls list 
urls = ['https://earthdata.nasa.gov/learn/user-resources/who-uses-nasa-earth-science-data-user-profiles/user-profile-dr-steven-d-miller',
"https://earthdata.nasa.gov/learn/user-resources/who-uses-nasa-earth-science-data-user-profiles/user-profile-dr-faisal-hossain",
'https://earthdata.nasa.gov/learn/user-resources/who-uses-nasa-earth-science-data-user-profiles/user-profile-dr-brian-barnes']

potentialApplications = []
potentialDOI = []

for url in urls: 
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')

    #gathers all of links mentioned in the user profiles 
    websites = soup.findAll('a', attrs={'href': re.compile("^http")})

    for item in websites:
        if 'youtu.be' not in item['href']:
            if 'nasa' in item['href']:
                potentialApplications.append(item['href'])
        if 'doi' in item['href']:
            potentialDOI.append(item['href'])

#used data frames for easier export to CSV (separate CSV files )
df = pd.DataFrame(potentialDOI,columns=['DOI links (publications/datasets)'])
apps = pd.DataFrame(potentialApplications, columns=['Potential Applications/NASA Assets'])

#print(df)
#print(apps)

#export to any filename you choose (change filenames to arguments in the future)
df.to_csv('userProfileDOI.csv')
apps.to_csv('userProfileApplications.csv')