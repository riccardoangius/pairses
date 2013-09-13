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
from pairseslib.wikipedia import *
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

if __name__ == '__main__':

	logging.basicConfig(filename=os.path.join(cfg['home'],'wikiread.log'), level=logging.DEBUG, format=cfg['logtimestampformat'])


	# Open the Wikipedia dump through wikidump 
	wikipediaDump = wikiModel.Dump('/Volumes/Data/wikidump/enwiki-20130304-pages-articles.xml',False,False)

	# Instantiate the English Wikipedia worder
	propertyWorder = EnglishWikipediaModule()

	text = wikipediaDump.get_page_contents_by_title('Bern').decode('utf-8')

	text = expandTemplates(text, propertyWorder)

	# Preliminary wiki markup cleanup
	text = WikiExtractor.clean(text)
	# Final wiki markup cleanup (turning text into a list of section titles and paragraphs)
	text = WikiExtractor.compact(text)
	
	for line in text:
		print(line.encode('utf-8'))