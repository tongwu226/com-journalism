import requests
import urllib
import unicodedata
import sys
import time
import pandas as pd
import datetime
import json
import urllib2
import simplejson
from googlesearch import GoogleSearch
from pprint import pprint
import math

def collect_autosuggestions(source, tld, lang, query):
	if source == "google":
		# Some info on this api: http://shreyaschand.com/blog/2013/01/03/google-autocomplete-api/
		url = 'http://www.google.'+tld+'/complete/search?&client=firefox&%s' % (urllib.urlencode({'q': query.encode('utf-8'), 'hl': lang}))
	elif source == "bing":
        # Note: for Bing the language is controlled by the tld, so the lang parameter will have no effect on its own
		url = 'http://api.bing.com/osjson.aspx?%s' % (urllib.urlencode({'query': query.encode('utf-8'), 'cc': tld}))
   
	r = requests.get(url)
	suggestions = r.json()[1]
	return suggestions

def unicode2str(text):
	return unicodedata.normalize('NFKD', text).encode('ascii','ignore')
	
def auto_suggestion_list(text):
	suggestions = collect_autosuggestions("google", "com", "en", text)
	ret = []
	for i in suggestions:
		ret.append(unicode2str(i))
	return ret

def top_search_results(text):
	gs = GoogleSearch(text)
	ret=[]
	for hit in gs.top_results():
		ret.append( (hit['title'], hit['content']) )
	return ret

def pnr(text):
	data = urllib.urlencode({"text": text}) 
	u = urllib.urlopen("http://text-processing.com/api/sentiment/", data)
	the_page = u.read()
	i = the_page.find("neg")
	neg = float(the_page[i+6:i+11])
	i = the_page.find("pos")
	pos = float(the_page[i+6:i+11])
	i = the_page.find("label")
	if ( the_page[i+9:i+12] == "pos" ):
		return 100*pos/neg
	elif ( the_page[i+9:i+12] == "neg" ):
		return -100*neg/pos
	return 0

def imp(text):
	gs = GoogleSearch(text)
	return 10*math.log10(gs.count())
	
def search_term_stat2(text):
	res=top_search_results(text)
	tot = 0
	for i in res:
		s = unicode2str(i[0])
		t = unicode2str(i[1])
		tot = tot+(2*pnr(s)+pnr(t))/3
	tot = tot/len(res)
	tot = (tot + pnr(text))/2
	return (tot, imp(text))

#from: http://stackoverflow.com/questions/1657570/google-search-from-a-python-app

def search_term_stat(searchfor):
	data = None
	
	while True:
		query = urllib.urlencode({'q': searchfor})
		url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' % query
		search_response = urllib.urlopen(url)
		search_results = search_response.read()
		results = json.loads(search_results)
		data = results['responseData']
		if ( data != None):
			break
		sys.stdout.write('.')
		sys.stdout.flush	
		time.sleep(1)
	
    #calculating the importance of the page
	page_importance = 10*math.log10(float(unicodedata.normalize('NFKD', data['cursor']['estimatedResultCount']).encode('ascii','ignore')))
    #estimating the sentiment in the top results
	hits = data['results']
	avg_sentiment = 0
	for h in hits:
		s = unicodedata.normalize('NFKD', h['title']).encode('ascii','ignore')
		t = unicodedata.normalize('NFKD', h['content']).encode('ascii','ignore')
		avg_sentiment = avg_sentiment + (2*pnr(s)+pnr(t))/3
	avg_sentiment = avg_sentiment / len(hits)
	return ("term sentiment:", pnr(searchfor),
            "page importance:", page_importance,
            "avg result sentiment:", avg_sentiment)
			
templates = [
    "? is ",
    "? is not ",
    "why ? ",
	"? hate ",
	"? should ",
]

candidates = [
    "hillary",
    "trump",
]

for cand in candidates:
	sum_sent = 0.0
	sum_imp = 0.0
	cnt = 0
	for tmpl in templates:
		search_term = tmpl.replace('?',cand)
		lst = auto_suggestion_list(search_term)
		tmp = [0.0,0.0,0.0]
		for i in lst:
			res = search_term_stat(i)
			print "           ", i, res[3], res[5]
			tmp[0] += res[3]
			tmp[1] += res[5]
			tmp[2] += 1
		
		if tmp[2] == 0:
			res = search_term_stat(search_term)
			tmp[0] = res[3]
			tmp[1] = res[5]
			tmp[2] = 1
		
		sum_imp += tmp[0]/tmp[2]
		sum_sent += tmp[1]/tmp[2]
		cnt += 1
		res = search_term_stat(search_term)
		print search_term, ": ", res[3], "  ", res[5], "     ", tmp[0]/tmp[2], " ", tmp[1]/tmp[2]
	print cand, sum_sent/cnt, sum_imp/cnt