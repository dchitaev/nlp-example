import json
import openai
import rollbar
import trafilatura
import xml.etree.ElementTree as ET
import tiktoken

from bs4 import BeautifulSoup


openai.api_key = %add your key%

with open("./assets/vertical_program_weighted.json", "r") as fp2:
    vertical_program_weighted = json.load(fp2)

with open("./assets/stopwords.txt", "r") as fp3:
    stopwords = [i.rstrip() for i in fp3.readlines()]

with open("./assets/punctuation.txt", "r") as fp4:
    punctuation = [i.rstrip() for i in fp4.readlines()]

#functions
def get_verticals_from_chatgpt(html_file, stopwords):
    result = []
    useful_text = trafilatura.extract(html_file, include_links=True, include_comments=False, output_format='xml')
    useful_text = ET.fromstring(useful_text)
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    blob = ''

    for element in useful_text.iter():
        if element.tag in ['p', 'item']:
            if element.text and element.text.strip():
                blob += element.text.strip() + ' '
            for child in element:
                blob += ET.tostring(child, encoding='unicode').strip() + ' '  

    size = 10000
    success = False
    
    while size >= 1000 and not success:
        blob_chunks = [
            "".join(encoding.decode(encoding.encode(blob)[i : i + size]))
            for i in range(0, len(encoding.encode(blob)), size)
        ]
        temp_result = []
        success = True
        
        for chunk in blob_chunks:
            request = """
            Imagine yourself as a travel blogger who wants to add at least 10 affiliate links to your text. Do not sentences that already contain links and <ref> tags.
            Do the following:
            1) Find suitable phrases to be wrapped with affiliate links. Consider coherence, relevance, and natural integration of the affiliate link. Each phrase consist of 2 to 6 consecutive and cohesive words without punctuation. If the phrase ends with stop words from '{1}' or a preposition, add the next words from the text for the phrase to be cohesive. Each phrase must include POI or final product, it could be a museum, hotel, attraction, city (for city tours, day tours, flights, car rentals), activity etc. It should be a proper name or category name.
            2) For each phrase, determine the most relevant topic from this list: Flights, Hotels, Tours and Activities, Car Rental, SIM-cards, Insurance, Bike rental, Food and Dining, Bus and train tickets, Sanatoriums, Transfers, Cruises, Boat Rental, Nightlife, Travel Gear, Sanatoriums, Bike Rental.
            3) Identify the final product or point of interest (POI) to which the affiliate link should lead. This could be a museum, attraction, city (for city tours, day tours, flights, car rentals), activity etc. Provide a name or short description of the POI and include location, not a list or URL.
            4) Rate the suitability of each placement by indicating your confidence level as "Low," "Medium," or "High".
            Format the results as a JSON object with the following keys:
            [{{"words": "phrase", "vertical": "topic", "poi": "final product or POI", "confidence": "Low or Medium or High"}}]
            Text:
            '{0}'
            """

            request = request.format(chunk, stopwords)

            try:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "user", "content": request}
                    ]
                )
                temp_result.extend(json.loads(completion.choices[0].message['content']))
            except:
                success = False
                break

        if success:
            result.extend(temp_result)
        else:
            size -= 1000

    return result

def check_verticals_from_chatgpt(gpt_dictionary):

    request = """
    You will be gigen a list, where each element represents placement of affiliate link in a travel blog.
    Each elemnt has words that will be wrapped into affiliate link, point of interest (poi) where the affiliate link should lead and vertical to which it relates.
    You have to check whether the poi and words are relevant to the vertical.
    Format the results as a JSON object with the following keys:
    [{{"words": "words", "vertical": "vertical", "poi": "poi", "confidence": "confidence", "relevance": "Yes or No"}}]
    List:
    '{0}'
            """

    request = request.format(gpt_dictionary)

    completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "user", "content": request}
                    ]
                )
    gpt_dictionary = json.loads(completion['choices'][0]['message']['content'])

    return gpt_dictionary

def check_gpt_results(gpt_dictionary, stopwords, punctuation,html_file):
    
    gpt_dictionary = check_verticals_from_chatgpt(gpt_dictionary)
    gpt_dictionary = [item for item in gpt_dictionary if item['relevance'] in ['Yes']]
    
    max_loops = 3
    loop_count = 0
    
    while loop_count < max_loops:
        to_exclude = []
        for el in gpt_dictionary:
            if el['words'].split()[-1] in stopwords or el['words'] in punctuation:
                to_exclude.append(el)
        
        if len(to_exclude) <= round(len(gpt_dictionary) * 0.2) and len(gpt_dictionary) - len(to_exclude) >= 10:
            gpt_dictionary = [el for el in gpt_dictionary if el not in to_exclude]
            break
        else:
            gpt_dictionary = get_verticals_from_chatgpt(html_file,stopwords)
        
        loop_count += 1
    
    return gpt_dictionary
                
def get_markup(html_file):
        
    # generate markup with ChatGPT
    gpt_dictionary = get_verticals_from_chatgpt(html_file, stopwords)
    # checking if results are correct
    gpt_dictionary = check_gpt_results(gpt_dictionary, stopwords, punctuation,html_file)

    return gpt_dictionary


# 2 blocks generation
def create_recommendation_blocks(html_file):
    result = {}
    soup = BeautifulSoup(html_file, 'html.parser')

    # get page metadata
    meta_text = get_meta_text(soup)

    # getting location, car rental relevance and nearest airport via ChatGPT
    #{"city":%city%,"country":%country%,"car rental":%yes or no%,"IATA":%IATA%}
    meta_location_data = get_meta_location_data(meta_text)

    if (len(meta_location_data)==0) or (type(meta_location_data) == str):
        return { "recommendation_blocks": [] }
    elif (meta_location_data['city'] is None) and (meta_location_data['country'] is None):
        return { "recommendation_blocks": [] }

    # Selecting best fit travel verticals
    page_verticals = '{}'
    page_vertical_program_weighted = get_page_vertical_program_weighted(page_verticals,vertical_program_weighted,meta_location_data)

    # Selecting brand to promoto for each vertical
    blocks_programs = get_blocks_programs(page_vertical_program_weighted)


    # Blocks text generation with basic checks
    texts = []
    
    for block in blocks_programs:
        max_loops = 3
        loop_count = 0
        text = ''
        while loop_count < max_loops:
            text = create_text_block(block['value'],meta_location_data)
            if len(text['header']) >= 10:
                if len(text['block1']) >= 300 and len(text['block2']) >= 300 and len(text['block1']) >= 300: 
                    texts.append({"block":block['block'],"text":text})
                    break
            loop_count +=1

    for block in texts:
        if len(block['text']['header']) < 10:
            raise Exception("The length of the header is too short")
        if len(block['text']['block1']) < 300 or len(block['text']['block2']) < 300 or len(block['text']['block1']) < 300: 
            raise Exception("The length of the blocks text is too short")

    result['recommendation_blocks'] = texts    
    
    return result

# Block generation via chatgpt
def create_text_block(block, meta_location_data):
    location = ''
    if meta_location_data['city'] is not None:
        location = meta_location_data['city']
    else:
        location = meta_location_data['country']

    request = '''Imagine yourself a travel blogger sharing useful services to your readers. You have to create header (about 40 symbols) and 3 text blocks (about 200-250 symbols each) to tell about travel products for people going to {0}.
    Explain why these product are cool and how to use them. Mention each product in a separate block and not more than 2 times. Don't create aggressive CTA. Also add 1-2 emojis to header and each block. List of products:
    1. {1},{2}
    2. {3},{4}
    3. {5},{6}
    Format answer as json only without new lines: {{"header":header,"block1":block1,"block2":block2,"block3":block3}}'''

    request = request.format(location
                             ,block[0]['vertical'],block[0]['program']
                             ,block[1]['vertical'],block[1]['program']
                             ,block[2]['vertical'],block[2]['program']
                            )
    try:
        completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": request}
        ]
        )

        result = completion.choices[0].message['content']
        result = json.loads(result)
    except:
        result = ''

    return result


# Selecting travel programs for blocks
def get_blocks_programs(page_vertical_program_weighted):

    result = []

    unused_items = [item for item in page_vertical_program_weighted if not item['used_on_page']]
    used_items = [item for item in page_vertical_program_weighted if item['used_on_page']]

    unused_items = sorted(unused_items, key=lambda x: x['weight'], reverse=True)
    used_items = sorted(used_items, key=lambda x: x['weight'], reverse=True)

    midblock_verticals = unused_items[:3]
    if len(midblock_verticals) < 3:
        midblock_verticals+=used_items[:3-len(midblock_verticals)]

    result.append({"block":"midblock","value":[{"vertical":item['vertical'],"program":max(item['programs'], key=lambda x: x['weight'])['program']} for item in midblock_verticals]})

    unused_items = [v for v in unused_items if v not in midblock_verticals]
    used_items = [v for v in used_items if v not in midblock_verticals]

    endblock_verticals = unused_items[:3]
    if len(endblock_verticals) < 3:
        endblock_verticals+=used_items[:3-len(endblock_verticals)]

    result.append({"block":"endblock","value":[{"vertical":item['vertical'],"program":max(item['programs'], key=lambda x: x['weight'])['program']} for item in endblock_verticals]})

    return result


# Weighting travel verticals
def get_page_vertical_program_weighted(page_verticals, vertical_program_weighted, meta_location_data):
    page_verticals = json.loads(page_verticals)

    page_vertical_program_weighted = vertical_program_weighted.copy()
    for vertical in page_vertical_program_weighted:
        if vertical['vertical'] == 'Car Rental':
            vertical['vertical'] = 'Car Rentals'
            if not meta_location_data['car rental']:
                vertical['weight'] = 0

    for weighted_vertical in page_vertical_program_weighted:
        weighted_vertical['used_on_page']=False
        if len(page_verticals) > 0:
            for page_vertical in page_verticals:
                if page_vertical['vertical'] == weighted_vertical['vertical']:
                    weighted_vertical['used_on_page']=True
                    for program in weighted_vertical['programs']:
                        for brand in page_vertical['brands']:
                            if brand == program['program']:
                                program['weight'] = 0

    return page_vertical_program_weighted

# Geting summary from page meta
def get_meta_location_data(meta_text):
    request = '''What cities and countries relates or are mentioned in the next text?
    {0}
    Then for most relevant city answer if you need to rent a car when visiting this location (use yes or no) and what is nearest airport's IATA.
    If only country is mentioned set city as "" and skip cars and airports. write answer strictly in this json format without any additional text: {{"city":%city%,"country":%country%,"car rental":%yes or no%,"IATA":%IATA%}}.
    Return only one answer for one given text.'''
    request = request.format(meta_text)

    completion = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[{ "role": "user", "content": request }]
    )
    
    rollbar.report_message("get_meta_location_data chatgpt request results", level='debug',
                           extra_data={'meta_text': meta_text, 'request': request, 'completion': completion})

    result = ''
    try:
        result = completion.choices[0].message['content']
        result = result.replace('"null"','null')
        result = result.replace("'null'",'null')
        result = result.replace('""','null')
        result = json.loads(result)
        if result['car rental'] == 'yes':
            result['car rental'] = True
        else:
            result['car rental'] = False
        return result
    finally:
        return result

def get_meta_text(soup):
    result = ''
    result += soup.find('title').text + ' '
    if soup.find('meta', attrs={'name': 'description'}):
        result += soup.find('meta', attrs={'name': 'description'})['content'] + ' '
    for tag in soup.find_all('meta'):
        if 'name' in tag.attrs and tag.attrs['name'].lower() in ['description', 'keywords', 'og:description', 'og:keywords']:
            result +=  tag.attrs['content'] + ' '
    return result