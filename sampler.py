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
import sys, os, re, traceback, logging, urllib2, argparse 
import networkx as nx
import WikiExtractor
from pairseslib import *
from unidecode import unidecode
from time import sleep
from httplib import BadStatusLine
from urllib2 import URLError
from englishWikiModule import EnglishWikipediaModule
from SPARQLWrapper.SPARQLExceptions import EndPointInternalError, EndPointNotFound
from time import strftime
from urllib2 import unquote
from pprint import pformat

startFrom = 0

# Debug
from pprint import pprint, pformat

def sampler(title, propertyWorder, wikipediaDump, sampleSentences):	

	language = propertyWorder.getLanguage()

	print('Working on `%s`' % title)

	projectedTitle = unquote(title.replace('_',' ')).decode(encoding='utf-8')
	primaryTitleLabels = {projectedTitle}
	
	print('Going with "%s"' % (projectedTitle))
	
	titleLabel = primaryTitleLabels.pop()

	############################################################################ 
	# 						Retrieve article for subject					   #
	print_n_flush('Retrieving article from Wikipedia...')

	# We do this instead, fetching the article from the wikipedia dump
	strTitleLabel = unidecode(titleLabel)
	
	try:
		rawArticle = wikipediaDump.get_page_contents_by_title(strTitleLabel)
	except KeyError:
		message = "Could not fetch the article for " + titleLabel
		logging.warning(message)
		print(message)
		return
	
	article = rawArticle.decode('utf-8')
	
	print 'OK'

	### Expand relevant templates in the Wikipedia article
	print_n_flush('Expanding relevant templates...')
	article = removeSectionTitles(article)
	article = expandTemplates(article, propertyWorder)

	print 'OK'	
	#END# Templates expansion

	### Wiki markup cleaning
	print_n_flush('Getting rid of wiki markup...')
	
	# Preliminary cleanup
	article = WikiExtractor.clean(article)
	# Final cleanup (turning text into a list of section titles and paragraphs)
	article = WikiExtractor.compact(article)

	print 'OK'
	#END# Wiki markup cleaning
	
	for paragraph in article:

		""" Account for a bug in the PunktSentenceTokenizer when handling
		 	sentence-ending marks followed by a double quote mark """
		paragraph = paragraph.replace('?"', '? "')
		paragraph = paragraph.replace('!"', '! "')
		paragraph = paragraph.replace('."', '. "')
		
		#TODO: Language-agnostic sentence tokenizer
		sentences = tokenize_sentence(paragraph)
		
		for sentence in sentences:
			sentence = propertyWorder.adjustText(sentence)
			sampleSentences.append(sentence)


if __name__ == '__main__':

	# Open the Wikipedia dump through wikidump 
	wikipediaDump = wikiModel.Dump(cfg['wikidumppath'], False, False)

	# Instantiate the English Wikipedia worder
	propertyWorder = EnglishWikipediaModule()

	clear_screen()
	articles = open(cfg['articletitleslistfile'])
	#articles = ['New_York_City']
	
	currentArticle = -1
	sampleSentences = list()
	
	for line in articles:
		currentArticle += 1

		if currentArticle < startFrom:
			continue
	
		title = line.replace('\n','')
	
		print_n_flush('\n' + unicode(currentArticle) + ':')
	
		processNext = False
		counter = 0
		while not processNext:
			try: 
				processNext = False
				sampler(title, propertyWorder, wikipediaDump, sampleSentences)
				processNext = True
				
			except (TimeoutError, BadStatusLine, URLError, EndPointInternalError, EndPointNotFound):
				print_n_flush('It looks like your connection is down, trying again in 120 seconds...\n')
				print('\a'*3)
				sleep(120)

				continue
				
			except KeyboardInterrupt:
				if checkLog:
					print('Something went wrong, please check your error log.')
				print >>sys.stderr, "Bye."
				exit()
				
	pickleDump(sampleSentences,'sampleSentences.obj')