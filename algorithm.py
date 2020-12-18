import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import csv 

#This script goes through a list of applications, and finds potential NASA datasets that the application uses. 
#All functions with 'get_' have to do with web scraping an applications and saving variables. Those variables 
#are then used as parameters to build CMR query links. The outputs of the query links are the datasets (name and link). 

applications_list = []

#maybe change the CSV file to an argument? 
with open('algo-input.csv', newline='') as input: # Open file in read mode
    for row in csv.reader(input):
        applications_list.append(row[0]) 

#rows is the only global variable - final 'table' that will be fed into the CSV output file 
rows = []

#searches contents of application website for a potential dataset shortname 
def get_shortName(soup, data):

    list_of_shortNames = ["MCD14DL", "MCD14ML","VNP14", "MCD64A1", "MOD14", "MOD14A1",
     "MOD14A2", "MYD14", "MYD14A1", "MYD14A2", "VNP03MODLL", "VNP14", "VNP14A1", "VNP64A1", "MCD12Q1"]
    potential_shortName = ''

    for name in list_of_shortNames:
        if name in data:
            potential_shortName = name

    #some applications may have the shortname as a hyperlink 
    for link in soup.find_all('a'):
        for name in list_of_shortNames:
            if name == link.get_text():
                potential_shortName = name
        
    return potential_shortName

#if application uses a DOI link, then count it as a publication within CSV output    
def get_publication(soup):
    publication = ''

    websites = soup.findAll('a', attrs={'href': re.compile("^http")})
    for link in websites:
        #if doi is in the application url (ex: https://doi.org/10.3334/ORNLDAAC/1509)
        if 'doi' in link['href']:
            publication = link['href']

    if len(publication) == 0:
        publication = "None"

    return publication

#searches for instrument name within application 
def get_instruments(data):
    instrument_names = ["MODIS", "VIIRS", "AIRS", "MOPITT", "OMI", "OMPS", "TROPOMI", 
    "AMSR2", "AMRSR-E", "OLI", "ECOSTRESS","SRTM", "TMPA", "PALSAR", "AVIRIS-NG", 
    "Hyperion", "ATLAS", "GEDI", "SAR", "ASTER", "UAVSAR", "PRISM", "ETM", "OLCI", "TIR", 
    "GLISTIN-A", "AMR", "TMR", "ACC", "SCA", "GLAS", "PALSAR", "DDMI", "AirSWOT", "ETM+", "TIRS", "MSI"]

    #collecting multiple instrument names, could be useful in algorithm refinement 
    potential_instrumentName = []
    instrument_name = ''

    for name in instrument_names:
        if name in data:
            potential_instrumentName.append(name)

    if len(potential_instrumentName) != 0:
        instrument_name = potential_instrumentName[0]

    return instrument_name

#searches for platform/satellite name within application
def get_platform(data):
    platform_names = ["Terra", "Aqua", "Suomi-NPP", "Shizuku", "GRACE", 
    "Landsat 8", "ISS", "SMAP", "ALOS", "Airborne", "EO-1", "GCOM-W1", "ICESat-2", "Sentinel-1", 
    "Aura", "Sentinel-5P", "Sentinel-2", "Sentinel-3", "Sentinel-6", "OMG", "TOPEX", "GRACE-FO", "JPSS", "CYGNSS", "SAC", "GPM", 
    "TRMM","IMERG"]

    #collecting multiple platform names, could be useful in algorithm refinement 
    potential_platformName = []
    platform_name = ''
    for name in platform_names:
        if name in data:
            potential_platformName.append(name)

    if len(potential_platformName) != 0:
        platform_name = potential_platformName[0]
    else:
        platform_name = ''

    return platform_name

#checks if near-real time is mentioned in application (could be a query variable)
#this is a key identifier in terms of filtering potential dataset matches, and most applications will probably use NRT 
def get_nrt(data):
    nrt = "near real"
    query_nrt = ""

    if nrt in data.lower():
        query_nrt = "NEAR_REAL_TIME"
    
    return query_nrt

#assigns topic to each application
def get_topic(data):
    #this list could be more exhaustive 
    application_topics = ['flood', 'fire', 'landslide', 'water', 'air', 'ecology', 'energy', 'hurricane', 'cyclone']
    app_topic = []
    topic = ''

    for topic in application_topics:
        if topic in data.lower():
            app_topic.append(topic)

    if len(app_topic) != 0:
        #included as a stylistic choice (more aesthetic for front-end) 
        #wasn't able to get the list comparison to work with certain topics 
        if app_topic != 'air' or app_topic != 'energy' or app_topic != 'ecology' or app_topic != 'water':
            topic = app_topic[0].capitalize() + "s"
    else:
        topic = "Miscellaneous"

    return topic 

#gets the name of the application 
def get_application_title(soup):
    title_find = soup.find('title')
    title = title_find.string

    if len(title) == 0:
        title = 'None'

    return title 

#extracts description of applciation - NEEDS TO BE MODIFIED (possibly use NLP or look at descriptions.py for additional methods)
def get_description(data):
    keywords = ['hurricane', 'hurricanes', 'earthquakes','earthquake', 'landslide', 'landslides','fire','fires', 
    'floods', 'flood', 'landslide', 'landslides', 'air', 'water', 'lightning','snow', 'volcano', 'cloud'
    'earthquake', 'ocean']
    description = ""
    sentences = data.split(".")

    for sentence in sentences:
        for keyword in keywords:
            if keyword in sentence:
                description = sentence
            elif keyword not in sentence:
                description = sentences[0]
            else: #certain applications may through an error because the sentences weren't able to be parsed, so default to an empty string 
                description = ""

    return description 

#gets keywords for query (searches for certain keywords within application)
def get_keywords(data):
    measurements = ['aerosol optical depth', 'aod', 'aot', 'burn serverity', 'air pollution', 
    'plume height', 'air quality',  'water quality', 'smoke detection', 'active fire']
    natural_phenomenons = ['hurricane', 'hurricanes', 'earthquakes','earthquake', 'landslide', 'landslides','fire','fires', 
    'floods', 'flood', 'landslide', 'landslides', 'air', 'water', 'lightning','snow', 'volcano', 'cloud'
    'earthquake', 'ocean']
    general_measurements = ['thickness', 'humidity', 'temperature', 'surface', 'precipitation']

    specific_measure = ''
    phenomenon = []
    measurement = ''
    keyword = ''

    #modified to this method of comparing against multiple lists, since comparing to just one combined list yielded too many keywords
    #too many keywords can lead to no query output, so limiting the keywords yet being specific is the goal! 

    #if a specific measurement was found, then keep that as a keyword 
    for name in measurements:
        if name in data.lower():
            specific_measure = name

    for name in natural_phenomenons:
        if name in data.lower():
            phenomenon.append(name)

    for name in general_measurements:
        if name in data.lower():
            measurement = name
    
    if len(specific_measure) != 0:
        keyword = specific_measure
    else:
        #combine the general measurements and natural phenomenons to get a more specific search 
        if len(phenomenon) != 0 and len(measurement) != 0:
            keyword = phenomenon[0] + "+" + measurement
        elif len(phenomenon) != 0:
            keyword = phenomenon[0]

    return keyword 

#creates the CMR query links by combining all scraped variables together 
def build_query_links(soup, data, application_url):

    shortName = get_shortName(soup, data)
    potential_platformName = get_platform(data)

    #special cases for platform names (need to account for more humanizers, maybe transform into another function)
    if potential_platformName == "Sentinel-1":
        potential_platformName = "Sentinel-1A"
    if potential_platformName == "Landsat 8":
        potential_platformName = "Landsat-8"

    potential_instrumentName = get_instruments(data)
    keywords = get_keywords(data)
    nrt = get_nrt(data)

    #adding parameters + variables to these links 
    base_url = 'https://cmr.earthdata.nasa.gov/search/collections?' 
    url = 'https://cmr.earthdata.nasa.gov/search/collections?' 
    query_links = [] #append the query links to this list 
    
    #dictionary of all relationships between platforms and instruments
    platform_instrument_relations = {'Terra':['ASTER', 'CERES', 'MISR', 'MODIS', 'MOPITT'], 
    'Aqua':["MODIS", "AMSU-A1", "AIRS", "AMSU-A2", "HSB", "CERES(2)"], "Suomi-NPP":["ATMS", "CERES", "CrIS", "OMPS", "VIIRS"], 
    "GCOM-W1":["AMSR2"], "GRACE":["KBR", "USO", "ACC", "SCA", "CES", "MTA", "GPS", "GSA"], "ALOS":["PALSAR-2"], "EO-1":["ALI", "HYPERION", "LAC"], 
    "TOPEX":["GPS", "LRA", "DORIS", "NRA"], "JPSS":["ATMS", "CERES", "CrIS", "OMPS", "VIIRS"], "CYGNSS":["DDMI"], "GPM":["DPR", "GPI"], 
    "TRMM":["TMI", "PR", "LIS", "CERES", "VIRS"], "Landsat-8":["OLI"], "Sentinel-1A":["SAR"]}
 
    if len(shortName) != 0:
        url = url + 'short_name=' + shortName
    
    else:
        #only add to the query link if the instrument and platform go together 
        if len(potential_instrumentName) != 0:
            for key in platform_instrument_relations:
                if key == potential_platformName:
                    for value in platform_instrument_relations[key]:
                        if value == potential_instrumentName:
                            url = url + '&platform=' + potential_platformName + '&instrument='+ potential_instrumentName
                            query_links.append(url)
            
            #otherwise, only add the instrument name in the query 
            if '&instrument=' not in url:
                url = url + '&instrument='+ potential_instrumentName
                query_links.append(url)

        #if the instrument name doesn't exist, then add the platform name 
        if len(potential_instrumentName) == 0 and len(potential_platformName) != 0:
            url = url + '&platform=' + potential_platformName
            query_links.append(url)

        #keep appending the variables found to form the most descriptive query 
        if len(keywords) !=0:
            url = url + '&keyword=' + keywords
            query_links.append(url)
            #one of the query links will just be of the keywords found (this at least guarentees some type of dataset output)
            additional = base_url + '&keyword=' + keywords
            query_links.append(additional)

        if len(nrt) !=0:
            url = url + '&collection_data_type=' + nrt 
            query_links.append(url)
    
    #removes duplicate query links
    query_links = list(dict.fromkeys(query_links))

    return query_links 

#runs all of the query links + adds them as rows 
def make_query(soup, data, application_url):
    query_links = build_query_links(soup, data, application_url)

    dataset_title = ''
    dataset_link = ''
    queryLink_matching = {}

    #call non-query variable functions 
    topic = get_topic(data)
    app_name = get_application_title(soup)
    publication = get_publication(soup)
    description = get_description(data)

    #start building the row dictionary for every application-dataset relationship 
    row = {'Topic':topic, 'Name':app_name, 'Site':application_url, 'Publication':publication}

    for url in query_links: 
        output = requests.get(url = url) #contents of the query output 
        datasets = {}
        url = url 

        #parses through CMR XML returned contents 
        root = ET.fromstring(output.content)
        #create dictionary with datasets (dataset name, dataset link)
        for child in root.iter('references'):
            for elem in child.iter():
                if elem.tag == 'name':
                    dataset_title = "{}".format(elem.text)
                if elem.tag == 'location':
                    dataset_link = "{}".format(elem.text)
                datasets[dataset_title] = dataset_link

        try:
            del datasets['']
        except KeyError:
            pass
        
        #creates another dictionary with the query link as the key, and the datasets dictionary as the value 
        queryLink_matching[url] = datasets

    for url, datasets in queryLink_matching.items():
        row = {'Topic':topic, 'Name':app_name, 'Site':application_url, 'Publication':publication, 'Application Description':description, 'Query Link': url}
        for key in datasets:
            row['Dataset Title'] = key
            row['Dataset LP'] = datasets[key]
        rows.append(row) #appends only the first value of the query output for each query link 
 
        
#transforms rows list into CSV file (maybe change CSV files to arguments)
def makecsv(rows):
    with open("algo_output.csv", "w") as csvfile:
        csv_fields = ['Topic', 'Name', 'Site', 'Publication', 'Application Description', 'Query Link', 'Dataset Title', 'Dataset LP']
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()
        for item in rows:
            writer.writerow(item)

#goes through all functions (until make_query) for every applicaiton in input file - ie: main function 
for url in applications_list:
    application_url = url
    
    req = requests.get(application_url)

    soup = BeautifulSoup(req.text, 'html.parser') #contains all of the tags, raw HTML 
    data = re.sub(r'</*?>','', soup.text) #contains only the text between tags in HTML 

    make_query(soup, data, application_url)

makecsv(rows)

