# Automated Web Harvesting for Usage-based Discovery 

These scripts were created in order to find new applications, and to find potential dataset matches. pathfinders.py and userprofiles.py extract links from NASA assets, while algorithm.py requires in CSV input of application links, and outputs application-dataset relationship matches. For algorithm.py, here are some examples of application links: [Dartmouth Flood Observatory](https://floodobservatory.colorado.edu/), [Hazards and Population Mapper](https://apps.apple.com/us/app/hazards-population-mapper/id1092168898), and [Amazon Dashboard](http://globalfiredata.org/pages/amazon-dashboard/)

How to run files locally: 
- Clone this repository, and `$ cd` into the project directory 
- Change the names of the CSV file paths (for both input and output files)
- Install necessary packages like `$ pip3 install requests` (do the same for bs4, pandas) 
- Run any of the scripts like `$ python3 algorithm.py` 

