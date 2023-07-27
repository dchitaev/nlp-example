import os
import requests
from fake_useragent import UserAgent

import os.path
import site
site.addsitedir(os.path.join(os.path.dirname(__file__), '..'))

from lib.markup import get_markup, create_recommendation_blocks

dataset=[
    {'url':'https://www.10best.com/destinations/netherlands/amsterdam/nightlife/brew-pubs/'},
    {'url':'https://www.dreambigtravelfarblog.com/blog/venice-on-a-budget'},
    {'url':'https://www.chasingthedonkey.com/dos-and-donts-of-visiting-turkey-travel-blog/'},
    {'url':'https://www.thepoortraveler.net/2017/06/singapore-travel-guide/'},
    {'url':'https://www.heatheronhertravels.com/waterfalls-volcanoes-and-hiking-in-st-lucia/'},
    {'url':'https://agirlandherpassport.com/tips-for-driving-in-montenegro/'},
    {'url':'https://www.aluxurytravelblog.com/2023/05/11/unique-authentic-experiences-india-holiday/'},
    {'url':'https://www.chasingthedonkey.com/things-to-do-in-santorini-with-kids-and-families/'},
    {'url':'https://mexicocassie.com/museums-merida/'},
    {'url':'https://solopassport.com/6-day-trips-from-sydney-by-train/'},
    {'url':'https://likewhereyouregoing.com/las-vegas-tips-first-timers/'}
    ]

marker = 220662
version = "666"
results = []

def get_html(url):
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print((url + ': '+response.status_code))
            pass
    except:
        print("Failed to request page")
        pass

results = []

for page in dataset:
    result = {}
    result['url'] = page["url"]
    print(page["url"])
    html = get_html(page["url"])
    if html:
        result['markup'] = get_markup(html)
        result['blocks'] = create_recommendation_blocks(html)
    else:
        result['markup'] = 'Failed'
        result['blocks'] = 'Failed'
    results.append(result)

for result in results:
    print(result)