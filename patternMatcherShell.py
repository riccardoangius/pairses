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
import sys, os, re, traceback, logging, urllib2
import networkx as nx
import WikiExtractor
from pairseslib import *
from unidecode import unidecode
from time import sleep
from httplib import BadStatusLine
from urllib2 import URLError
from englishWikiModule import EnglishWikipediaModule
from nltk.tokenize import sent_tokenize
from time import strftime
from jsonrpclib.jsonrpc import ProtocolError

# Debug
from pprint import pprint

MAX_ARTICLES_TO_PARSE = 0

def patternMatcher(text, patterns, propertyWorder, sourceURL = ''):	

	language = propertyWorder.getLanguage()

	matchesSoFar = 0

	#TODO: Language-agnostic sentence tokenizer
	sentences = tokenize_sentence(text)

	for sentence in sentences:
		sentence = propertyWorder.adjustText(sentence)		

		# Parse the sentence through the Stanford NLP Core Tools
		try:
			(sentenceRootWord, sentenceW, sentenceG, sentence, sentenceWData) = annotateText(sentence, True)
		except AnnotationError:
			continue
	
		legalNodeIndices = map(lambda x: int(x[x.rindex("-")+1:]), sentenceG.nodes())
	
		rootNode = 'ROOT-0'
	
		subjectTag = cfg['subjecttag']
		objectTag = cfg['objecttag']
		rootTag = cfg['roottag']
		
		for pattern in patterns:
			
			patternG = pattern['graph']
			
			predicate = pattern['predicate']			
			
			if set(patternG.nodes()) <= {subjectTag, objectTag, rootTag}:
				continue
			
			# Subject path in pattern graph
			try: 
				subjectPath = nx.shortest_path(patternG, rootTag, subjectTag)
			except nx.NetworkXNoPath:
				"""Deal with Networkx's inability to deal with perfectly correct dot language"""
				continue
				
			# Labeled
			labeledSubjectPath = labelPath(patternG, subjectPath)
		
			matchingSubjectNodes = pathDestinations(sentence, sentenceG, sentenceWData, labeledSubjectPath, pattern['entities'], pattern['numericObject'], propertyWorder)
		

			if empty(matchingSubjectNodes):
				continue
			
			# Object path in pattern graph
			try: 
				objectPath = nx.shortest_path(patternG, rootTag, objectTag)
			except nx.NetworkXNoPath:
				"""Deal with Networkx's inability to deal with perfectly correct dot language"""
				continue
				
			# Labeled
			labeledObjectPath = labelPath(patternG, objectPath)
		
			matchingObjectNodes = pathDestinations(sentence, sentenceG, sentenceWData, labeledObjectPath, pattern['entities'], pattern['numericObject'], propertyWorder)
		
			
		
			if empty(matchingObjectNodes):
				continue

			for matchingSubjectNode in matchingSubjectNodes:

				try:
					foundSubject = associatedWording(sentence, matchingSubjectNode, sentenceG, sentenceWData, allowNestedWordingMatch=True)
				except AnnotationError:
					continue				

				for matchingObjectNode in filter(lambda x: x != matchingSubjectNode, matchingObjectNodes):

					try:
						foundObject = associatedWording(sentence, matchingObjectNode, sentenceG, sentenceWData, allowNestedWordingMatch=True)
					except AnnotationError:
						continue				
			
					if (foundSubject, foundObject) in pattern['sourcePairs']:
						matchesSoFar += 1
						print 'Matches so far: %d' % matchesSoFar
					else:
						print("\n\nIN %s\n(%s, %s, %s)" % (sentence, foundSubject,predicate,foundObject))
						print("FROM %s" % (pattern['hash']))
						match = Match(foundSubject, foundObject, predicate, pattern['hash'], sourceURL, sentence)
						pprint(labeledSubjectPath)

						pprint(labeledObjectPath)
						pprint(patternG.edges(data=True))
						pprint(sentenceG.edges(data=True))

if __name__ == '__main__':

	logging.basicConfig(filename=os.path.join(cfg['home'],'pairses.log'), level=logging.DEBUG, format=cfg['logtimestampformat'])


	# Open the Wikipedia dump through wikidump 
	wikipediaDump = wikiModel.Dump(	'/Volumes/Data/wikidump/enwiki-20130304-pages-articles.xml',
									False,False)

	# Instantiate the English Wikipedia worder
	propertyWorder = EnglishWikipediaModule()

	language = propertyWorder.getLanguage()
	
	useCached = True

	patterns = fetchPatterns()
	
	clear_screen()	
	while True:

		text = raw_input("> ")

		patternMatcher(text.decode(encoding='utf-8'), patterns, propertyWorder, '')