import json
import requests

def get_facet_intruments(data):
    instruments = []
    for i in range(len(data)):
        instruments.append(data[i]['title'])
    return instruments

def get_facet_platforms(data):
    platforms = []
    for i in range(len(data)):
        platforms.append(data[i]['title'])
    return platforms

def get_relations(instruments):
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.json?facets_size[platform]=10000&include_facets=v2"
    relations = {} 
    for instrument in instruments:
        url = base_url + "&instrument=" + instrument
        response = requests.get(url)
        data = response.json()
        data = data['feed']['facets']['children']
        index = get_index(data, 'Platforms')
        platforms = None
        if index != None:
            platforms = get_facet_platforms(data[index]['children'])
        relations[instrument] = platforms
        print("Got the Platforms for "+instrument+"!!!")
    return relations

def get_facets():
    url = "https://cmr.earthdata.nasa.gov/search/collections.json?facets_size[instrument]=10000&include_facets=v2"
    response = requests.get(url)
    data = response.json()
    data = data['feed']['facets']['children']
    index = get_index(data, 'Instruments')
    instruments = get_facet_intruments(data[index]['children'])
    print("Got the Instruments!!")

    url = "https://cmr.earthdata.nasa.gov/search/collections.json?facets_size[platform]=10000&include_facets=v2"
    response = requests.get(url)
    data = response.json()
    data = data['feed']['facets']['children']
    index = get_index(data, 'Platforms')
    platforms = get_facet_platforms(data[index]['children'])
    print("Got the Platforms!!")
    
    relations = get_relations(instruments)
    obj = {'instruments': instruments, 'platforms': platforms, 'relations': relations}
    
    json_obj = json.dumps(obj, indent=4)
    with open("facets.json", "w") as outfile:
        outfile.write(json_obj)

def get_index(data, facet):
    for i in range(len(data)):
        if data[i]['title'] == facet:
            return i
    return None

get_facets()
