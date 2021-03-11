import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from w3lib.html import remove_tags
import csv 
import lxml, lxml.html, lxml.html.clean
from nltk import tokenize
import json

applications_list = []

list_of_shortNames = ["MCD14DL", "MCD14ML","VNP14", "MCD64A1", "MOD14", "MOD14A1",
    "MOD14A2", "MYD14", "MYD14A1", "MYD14A2", "VNP03MODLL", "VNP14", "VNP14A1",
    "VNP64A1", "MCD12Q1"]

instrument_names = ["MODIS", "VIIRS", "AIRS", "MOPITT", "OMI", "OMPS", "TROPOMI", 
    "AMSR2", "AMRSR-E", "OLI", "ECOSTRESS","SRTM", "TMPA", "PALSAR", "AVIRIS-NG", 
    "Hyperion", "ATLAS", "GEDI", "SAR", "ASTER", "UAVSAR", "PRISM", "ETM", "OLCI",
    "TIR", "GLISTIN-A", "AMR", "TMR", "ACC", "SCA", "GLAS", "PALSAR", "DDMI",
    "AirSWOT", "ETM+", "TIRS", "MSI"]

platform_names = ["AIRCRAFT", "Aqua", "Aquarius_SAC-D", "Terra", "AURA", "Suomi-NPP", "Shizuku", "GRACE", "Landsat 8",
    "ISS", "SMAP", "ALOS", "Airborne", "EO-1", "GCOM-W1", "ICESat-2", "Sentinel-1", 
    "Aura", "Sentinel-5P", "Sentinel-2", "Sentinel-3", "Sentinel-6", "OMG", "TOPEX",
    "GRACE-FO", "JPSS", "CYGNSS", "SAC", "GPM", "TRMM","IMERG"]

overall = list_of_shortNames + instrument_names + platform_names

application_topics = ['flood', 'fire', 'landslide', 'water', 'air', 'hurricane',
    'cyclone', 'snowfall', 'lake height', 'agriculture', 'hazard', 'earthquake',
    'energy', 'soil moisture', 'storm', 'precipitation', 'river height', 'volcanoe']

keywords = ['hurricane', 'earthquake', 'landslide', 'fire', 'flood', 'landslide',
    'air', 'water', 'lightning', 'snow', 'volcano', 'cloud', 'ocean']

measurements = ['aerosol optical depth', 'aod', 'aot', 'burn severity', 'air pollution',
    'plume height', 'air quality',  'water quality', 'smoke detection', 'active fire']

natural_phenomenons = ['hurricane', 'earthquake', 'landslide', 'fire', 'flood',
    'landslide', 'air', 'water', 'lightning','snow', 'volcano', 'cloud', 'ocean']

general_measurements = ['thickness', 'humidity', 'temperature', 'surface', 'precipitation']

#dictionary of all relationships between platforms and instruments
platform_instrument_relations = {'Terra':['ASTER', 'CERES', 'MISR', 'MODIS', 'MOPITT'], 
'Aqua':["MODIS", "AMSU-A1", "AIRS", "AMSU-A2", "HSB", "CERES(2)"], "Suomi-NPP":["ATMS", "CERES", "CrIS", "OMPS", "VIIRS"], 
"GCOM-W1":["AMSR2"], "GRACE":["KBR", "USO", "ACC", "SCA", "CES", "MTA", "GPS", "GSA"], "ALOS":["PALSAR-2"], "EO-1":["ALI", "HYPERION", "LAC"], 
"TOPEX":["GPS", "LRA", "DORIS", "NRA"], "JPSS":["ATMS", "CERES", "CrIS", "OMPS", "VIIRS"], "CYGNSS":["DDMI"], "GPM":["DPR", "GPI"], 
"TRMM":["TMI", "PR", "LIS", "CERES", "VIRS"], "Landsat-8":["OLI"], "Sentinel-1A":["SAR"]}

stub = "https://search.earthdata.nasa.gov/search?"

switch = {
    'features': 'ff=',
    'platforms': 'fp=',
    'instruments': 'fi=',
    'organizations': 'fcd=',
    'projects': 'fpj=',
    'processing_levels': 'fl=',
    'data_format': 'gdf=',
    'tiling_system': 's2n=',
    'horizontal_data_resolutoin': 'hdr='
}

#gets keywords for query (searches for certain keywords within application)
def get_keywords(data):
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
    publications = get_publications(soup)
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
 
def build_search_url(keywords):
    search_url = stub
    for category in keywords:
        search_url += switch.get(category)
        for each in category:
            search_url += each + '!'
        search_url += '&'
    return search_url

def get_shortNames(soup, data):
    shortNames = []
    for name in list_of_shortNames:
        if name in data:
            shortNames.append(name)
    #some applications may have the shortname as a hyperlink 
    for link in soup.find_all('a'):
        for name in list_of_shortNames:
            if name == link.get_text():
                shortNames.append(name)
    return shortNames

def get_instruments(data):
    #collecting multiple instrument names, could be useful in algorithm refinement 
    instruments = []
    for name in instrument_names:
        if name in data:
            instruments.append(name)
    return instruments

def get_platforms(data):
    #collecting multiple platform names, could be useful in algorithm refinement 
    platforms = []
    for name in platform_names:
        if name in data:
            platforms.append(name)
    return platforms

def get_nrt(data):
    return "near real" in data.lower() or "nrt" in data.lower()

def get_topic(data):
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
    title = soup.title.text
    return title 

def get_sentences(data):
    sentences = tokenize.sent_tokenize(data)
    return sentences

def get_words(data):
    words = set(re.split("[^\w-]+", data))
    return words

def get_description(sentences):
    description = ""
    for sentence in sentences:
        if len(re.split("\s", sentence)) > 5 and len(re.findall("\.", sentence)) < 3:
            found = False
            for keyword in keywords:
                if not found and keyword in sentence.lower():
                    description += sentence + " "
                    found = True
    return description.strip()

def get_publications(sentences, soup):
    publications = []
    websites = soup.findAll('a', attrs={'href': re.compile("^http")})
    for link in websites:
        if 'doi' in link['href'] and link['href'] not in publications:
            publications.append(link['href'])
    for sentence in sentences:
        if 'doi:' in sentence:
            sentence = sentence[sentence.find('doi'):]
            sentence = sentence.replace("doi:", "https://doi.org/")
            if sentence[-1] == '.':
                sentence = sentence[:-1]
            if sentence not in publications:
                publications.append(sentence)
    return publications

def get_other(data, keywords):
    other = {'words': [], 'datasets': []}
    covered = []
    words = get_words(data)
    for word in words:
        if re.match("[A-Z]{3,8}_*\d*[A-Z]*\d*", word) and word not in keywords:
            covered.append(word)
            result = get_other_cmr(word)
            if result:
                other['words'].append(word)
                other['datasets'].append(result)
    return other

def get_other_cmr(word):
    url = "https://cmr.earthdata.nasa.gov/search/collections?&keyword="+word
    response = requests.get(url)
    root = ET.fromstring(response.content)
    hits = int(root.find("hits").text)
    if hits == 0 or hits > 15:
        return None
    datasets = {}
    for reference in root.find('references'):
        dataset_title = ""
        dataset_link = ""
        for elem in reference:
            if elem.tag == 'name':
                dataset_title = elem.text
            if elem.tag == 'location':
                dataset_link = elem.text
        datasets[dataset_title] = dataset_link
    return datasets

def makedict(site, soup, data):
    sentences = get_sentences(data)
    keywords = get_keywords(data)
    result = {}
    result['site'] = site
    result['topic'] = get_topic(data)
    result['name'] = get_application_title(soup)
    result['description'] = get_description(sentences)
    result['publications'] = get_publications(sentences, soup)
    result['instruments'] = get_instruments(data)
    result['platforms'] = get_platforms(data)
    result['shortnames'] = get_shortNames(soup, data)
    result['nrt'] = get_nrt(data)
    other = get_other(data, result['instruments']+result['platforms']+result['shortnames'])
    result['other_words'] = other['words']
    result['other_datasets'] = other['datasets']
    return result

def autofill(url):
    print(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser') #contains all of the tags, raw HTML 
    cleaner = lxml.html.clean.Cleaner(
        scripts = True,
        javascript = True,
        comments = False,
        style = True,
        inline_style = True,
    )
    html = lxml.html.document_fromstring(response.text)
    html_clean = cleaner.clean_html(html)
    data = lxml.html.tostring(html_clean)
    data = remove_tags(data)
    #remove html entities like &#13;
    data = re.sub("&\W*\w{2,4};", "", data)
    data = re.sub("\n", " ", data)
    data = re.sub("\s\s+", " ", data)
    result = makedict(url, soup, data)
    print(json.dumps(result, indent=4, sort_keys=True))
    return result

autofill("http://flood.umd.edu/")
autofill("http://floodobservatory.colorado.edu/Events/4827/2019Philippines4827.html")
autofill("http://www.globalfiredata.org/analysis.html")
autofill("https://cropmonitor.org/index.php/eodatatools/cmet/")
autofill("https://essd.copernicus.org/articles/12/137/2020/")
autofill("https://maps.disasters.nasa.gov/arcgis/apps/MapSeries/index.html?appid=2ba3d55f1d924ebc89cb8914ab4d138a")
autofill("https://webmap.ornl.gov/ogc/dataset.jsp?ds_id=1321")
