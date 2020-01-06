#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# =============================================================================
#  Version: 0.1 (September 14, 2013)
#  Author: Riccardo Angius (riccardo.angius@me.com)
#
# =============================================================================
#  Copyright (c) 2013. Riccardo Angius (riccardo.angius@me.com)
# =============================================================================
#  This file is part of Pairses: A PAttern Induced RDF Statement Extraction System.
#
#  This is fairly beta software. Please contact the author before usage.
# =============================================================================
from timeout import timeout
import nltk.data
import json, urllib2, re
from pprint import pprint
import requests

@timeout(60)
def getWikiArticleRevision(sourceWiki, revisionNo):
	wikiUrl = 'http://' + sourceWiki + '.wikipedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&revids=' + revisionNo
	wikiHandle = urllib2.urlopen(wikiUrl)
	return wikiHandle
	
@timeout(60)
def getCurrentWikiArticleRevision(sourceWiki, title):
	wikiUrl = 'http://' + sourceWiki + '.wikipedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=' + title
	wikiHandle = urllib2.urlopen(wikiUrl)
	return wikiHandle
	
def getCurrentWikiArticleText(sourceWiki, title):
	print('Getting Wikipedia article...')	
	wikiHandle = getCurrentWikiArticleRevision(sourceWiki, title)

	wikiFile = wikiHandle.read()
	wikiData = json.loads(wikiFile)

	print('Getting properties...')
	try:
		return wikiData['query']['pages'].values()[0]['revisions'][0]['*']

	except KeyError:
		print('Could not find this page in Wikipedia!')

def expandTemplate(propertyWorder, match):	
	payload = match.group('payload')
	components = payload.split('|')
	templateName = components.pop(0)
	templateName = templateName.lower()
	
	if len(components) < 1:
		"""Account for usage of a template solely for instruction purposes in comments"""
		expansion = unicode()
		
	elif templateName == 'convert':
		expansion = propertyWorder.expandTemplateConvert(components)

	elif templateName == 'ipa':
		"""http://en.wikipedia.org/wiki/Template:IPA"""
		expansion = components[0]

	elif templateName.startswith('ipa-') or templateName.startswith('ipac-'):
		"""http://en.wikipedia.org/wiki/Template:IPAc-en"""
		extras = ['icon', 'lang', 'english', 'pron', 'pronunciation', 'local', 'ipa', 'us', 'uk', '-']
		chars = [unicode(item) for item in components if item not in extras and '.ogg' not in item]
		expansion = u''.join(chars)
		expansion = u'/' + expansion + u'/'

	elif templateName == 'transl':
		"""http://en.wikipedia.org/wiki/Template:Transl"""
		expansion = components[-1]

	elif templateName == 'lang':
		expansion = components[-1]
	
	elif templateName.startswith('lang-'):
		extras = ['links=no']
		words = [unicode(item) for item in components if item not in extras]
		expansion = words[-1]
	
	elif templateName == 'as of':
		# TODO: Expand months and days, when present, as well 
		year = components.pop(0)
		expansion = templateName + ' ' + year
		
	elif templateName == 'nhly' or templateName == 'nhl year':
		"""http://en.wikipedia.org/wiki/Template:NHL_Year"""
		year = int(components.pop(0))
		followingYear = year+1
		expansion = unicode(year) + u'-' + unicode(followingYear)

	else:
		expansion = unicode()
		# Debug
		#expansion = payload
		
	return expansion
	
def expandTemplates(text, propertyWorder):
	template = re.compile(r'\{\{(?P<payload>.*?)\}\}')
	return template.sub(lambda match: expandTemplate(propertyWorder, match), text)

def removeSectionTitles(text):
	section = re.compile(r'(==+)\s*(.*?)\s*\1')
	return section.sub('', text)

# Initialize the sentence tokenizer from the NLTK tools
# Unfortunately this limits correct tokenizing to English text
# TODO: require LocalisedWikiModule to include a string for identifying the right tokenizer
sentence_splitter = nltk.data.load('tokenizers/punkt/english.pickle')

def tokenize_sentence(text):
	tokens = sentence_splitter.tokenize(text)
	return tokens