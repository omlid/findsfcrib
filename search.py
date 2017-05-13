import pandas as pd
import requests
import googlemaps
from bs4 import BeautifulSoup
import re
import datetime

search_url_base = "https://sfbay.craigslist.org/search/sfc"
listing_url_base = "https://sfbay.craigslist.org"

user_dict = {
	"Erik": (2500,3500,'185 Berry St'),
	"Josh": (1400,1500,'760 Market St'),
	"Rye": (1400,1500)
}

min_budget = sum([i[0] for i in user_dict.values()])
max_budget = sum([i[1] for i in user_dict.values()])

params = {
	"min_bedrooms":3,
	"min_bathrooms":2,
	"max_price":max_budget,
	"min_price":min_budget,
	"pets_dog": 1
}


#Do no revisit the same post
visited = {}

rsp = requests.get(search_url_base, params=params)
search_results = BeautifulSoup(rsp.text, 'html.parser')
listing_url_regex = re.compile(r'/sfc/apa/\d?')
selected_urls = list(set(filter(listing_url_regex.search,[link.get('href') for link in search_results.find_all('a')])))

queue = []
queue = queue + selected_urls

def find_crib_details(crib_path):
	global listing_url_base
	crib_html = requests.get(listing_url_base + crib_path)
	crib_soup = BeautifulSoup(crib_html.text,'html.parser')
	try:
		title = str(crib_soup.title.string)
	except:
		title = None
	try:
		price = str(crib_soup.find_all('span','price')[0].string)
	except:
		price = None
	try:
		bedrooms = str(crib_soup.find_all('p','attrgroup')[0].find_all('b')[0].string)
	except:
		bedrooms = None
	try:
		bathrooms = str(crib_soup.find_all('p','attrgroup')[0].find_all('b')[1].string)
	except:
		bathrooms = None
	try:
		laundry = crib_soup.find_all('p','attrgroup')[1].find_all(string=re.compile(r'(w/d)|(laundry)'))[0].string
	except:
		laundry = None
	try:
		mapaddress = crib_soup.find_all('div',class_="mapaddress")[0].string
	except:
		mapaddress = None
	return (title, price, bedrooms, bathrooms, laundry, mapaddress, crib_path)

def get_next_result_page():
	global search_results
	global rsp
	try:
		next_page_path = str(search_results.find_all('a',class_="button next")[0]['href'])
		rsp = requests.get(search_url_base+next_page_path)
		search_results = BeautifulSoup(rsp.text, 'html.parser')
		selected_urls = list(set(filter(listing_url_regex.search,[link.get('href') for link in search_results.find_all('a')])))
		return selected_urls
	except IndexError:
		pass


data = {
	"title":[],
	"price":[],
	"bedrooms":[],
	"laundry":[],
	"mapaddress":[],
	"crib_path":[]
}

while len(queue) > 0:
	check_out_crib = queue.pop()
	if check_out_crib in visited:
		continue
	else:
		title, price, bedrooms, bathrooms, laundry, mapaddress, crib_path = find_crib_details(check_out_crib)
		data['title'].append(title)
		data['price'].append(price)
		data['bedrooms'].append(bedrooms)
		data['laundry'].append(laundry)
		data['mapaddress'].append(mapaddress)
		data['crib_path'].append(crib_path)
		visited.update({check_out_crib:True})
		next_page = get_next_result_page()
		next_page = list(filter(lambda x: (x in visited) == False,next_page))
		queue = queue + next_page
		print(len(queue))
		print(len(visited.keys()))




file_name_bro=datetime.datetime.now().strftime("%Y%m%d%H%M%S")+'_cribs.csv'
print 'results/'+file_name_bro

df = pd.DataFrame(data)
df.to_csv('results/'+file_name_bro)

#class = result-row gets you all the lists
#Class = "attrgroup" will tell you the pets and washer/dryer/dishwasher/parking situation
#Class = "mapaddress" will tell you the address --> feed address into Google Maps API to get number of transfers - estimated commute time
