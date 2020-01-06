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
import sys, os, re, traceback
import traceback, urllib2
import WikiExtractor
from pprint import pprint
from unidecode import unidecode
from pairseslib.stanfordcorenlp import StanfordCoreNLP
from pairseslib.classes import *
from string import join
from pairseslib.timeout import TimeoutError
from pairseslib.configuration import *
from pairseslib.common import *
from time import sleep
from httplib import BadStatusLine
from urllib2 import URLError
from englishWikiModule import EnglishWikipediaModule
from nltk.tree import Tree
from jsonrpc import RPCInternalError
from nltk.tokenize import sent_tokenize
import networkx as nx
from pairseslib import *
from pairseslib.wikidump import model as wikiModel
from time import strftime
import logging

def naivepatternHarvester(title, propertyWorder, wikipediaDump, naivePredicateStatistics, naiveSubjectStatistics):
	language = propertyWorder.getLanguage()
		
	print('Working on `' + title + '`')
 
	# Get triples from DBPedia
	print_n_flush('Querying DBPedia...')

	iri = '<' + namespaces['dbpedia'] + title + '>'
	dbpediaData = fetchSubjectTriples(iri,language)
	
	# End of DBPedia get triples
	print 'OK'
	
	sourceWiki = language;

	# Retrieve Wikipedia article
	print_n_flush('Retrieving article from Wikipedia...')
	
	# Obtain a pattern graph for the subject
	titleLabelSingleton = getPredicateValues(dbpediaData, 'rdfs:label')
	
	# We are pretty sure right now extendendSubjectLabels is a singleton (i.e. there is only one triple for predicate rdfs:label)
	try:
		assert(len(titleLabelSingleton) == 1)
	except:
		return
	titleLabel = iter(titleLabelSingleton).next()
	
	# We don't do this anymore
	# text = getCurrentWikiArticleText(sourceWiki, title)
	# We do this instead
	try:
		text = wikipediaDump.get_page_contents_by_title(unidecode(titleLabel)).decode('utf-8')
	except KeyError:
		print_n_flush('\nCould not find a page with this title: "' + unidecode(titleLabel) + '", skipping')
		return
		
		
	# End of Wikipedia article retrieving
	print 'OK'

	# Remove wiki markup
	print_n_flush('Getting rid of wiki markup...')
	
	# Preliminary wiki markup cleanup
	text = WikiExtractor.clean(text)
	# Final wiki markup cleanup (turning text into a list of section titles and paragraphs)
	text = WikiExtractor.compact(text)

	# End of wiki markup cleaning
	print 'OK'
	
	mergedText = u' '.join(text)
	naivepatterns.naiveStatistics(title, mergedText, dbpediaData, propertyWorder, naivePredicateStatistics, naiveSubjectStatistics, 3, False)

if __name__ == '__main__':

	logging.basicConfig(filename='logs/pairses-' + strftime(cfg['logdateformat']) + '.log', level=logging.DEBUG, format=cfg['logtimestampformat'])

	# Open the Wikipedia dump through wikidump 
	wikipediaDump = wikiModel.Dump('/Volumes/Data/wikidump/enwiki-20130304-pages-articles.xml',False,False)

	propertyWorder = EnglishWikipediaModule()

	clear_screen()

	articles = open(cfg['articletitleslistfile'])
	currentArticle = 0

	nlp = StanfordCoreNLP()

	naivePredicateStatistics = dict()
	naiveSubjectStatistics = list()

	#articles = ['Bingham,_Maine']

	for line in articles:
		title = line.replace('\n','')
	
		print_n_flush(unicode(currentArticle) + ':')
	
		processNext = False
	
		while not processNext:
			try: 
				naivepatternHarvester(title, propertyWorder, wikipediaDump, naivePredicateStatistics, naiveSubjectStatistics)
				processNext = True
			except (TimeoutError, BadStatusLine, URLError):
				print('It looks like your connection is down, trying again in 60 seconds...')
				sleep(60)
				continue
	
		currentArticle += 1
	


	subjectStatisticsOutput = open(cfg['naivesubjectstatisticsoutput'],'w')
	for line in naiveSubjectStatistics:
		subjectStatisticsOutput.write(line + '\n')

	naivePredicateStatisticsToHTML(naivePredicateStatistics)
