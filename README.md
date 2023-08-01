# Task
## 1. Genereate travel brands promo blocks
We have a travel blog page's HTML  as input
The output needs to be:
* Content for 2 blocks (title + 3 columns) with:
  * Travel brand verticals that are relevant to the page. For example, there's no need to suggest car rental in Venice or aggressively promote insurance purchases for an article about local travel. Let's start with these verticals: Tours and Activities, Hotels, Flights, Car Rental, SIM cards, Insurance, Bus and train tickets.
  * Geo POI related to the page

## 2. Find all POIs/keywords for monetization 
The input is a blog page's text. It can be obtained by trafilatura (https://trafilatura.readthedocs.io/) or any other way.

The task is to get:
* List of POIs mentioned on the page:
  * For each, determine what it is and which verticals are applicable for its monetization based on the POI itself and the context
* Select keywords suitable for monetization of verticals without POI
For example, eSIM or insurance

The result should look like this:
* CTA (words that can be wrapped in a link)
* Verticals applicable to the CTA
* The target for the CTA (what should we look for at the travel brand's site, like the hotel name of insurance for traveling in SEA)

# Launching
1. Add OpenAI key to markup.py
2. Laucn runner.py to get results
