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
from jsonrpclib.jsonrpc import ProtocolError
import logging
import sys
from pairseslib.pickling import pickleDump, pickleLoad

currentArticle = 0
language = 'en'
if __name__ == '__main__':
	articles = open('sampleCities.txt')

	for line in articles:
		title = line.replace('\n','')
	
		print_n_flush('\n' + unicode(currentArticle) + ': ' + title)
	
		processNext = False
	
		while not processNext:
			try: 
				iri = '<' + namespaces['dbpedia'] + title + '>'
				dbpediaData = fetchSubjectTriples(iri,language)
				otherNames(iri,language)
				
				processNext = True
			except (TimeoutError, BadStatusLine, URLError):
				print_n_flush('It looks like your connection is down, trying again in 60 seconds...')
				sleep(60)
				continue
		
		currentArticle+=1
	articles.close()