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
from pprint import pprint, pformat

MAX_ARTICLES_TO_PARSE = 0

def patternMatcher(text, patterns, propertyWorder, sourceURL = '', presplit = False):	

	i = 0

	language = propertyWorder.getLanguage()

	trivialMatches = 0

	if presplit:
		sentences = text
	else:
		sentences = tokenize_sentence(text)

	for (j, sentence) in enumerate(sentences, 1):
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
					extractedSubject = associatedWording(sentence, matchingSubjectNode, sentenceG, sentenceWData, allowNestedWordingMatch=True)
				except AnnotationError:
					continue				

				for matchingObjectNode in filter(lambda x: x != matchingSubjectNode, matchingObjectNodes):

					try:
						extractedObject = associatedWording(sentence, matchingObjectNode, sentenceG, sentenceWData, allowNestedWordingMatch=True)
					except AnnotationError:
						continue				
			
					"""
					try:
						(ESRootWord, ESW, ESG, extractedSubject, ESWData) = annotateText(extractedSubject, True)
						(EORootWord, EOW, EOG, extractedObject, EOWData) = annotateText(extractedObject, True)
					except AnnotationError:
						continue
		
					ESNET = ESWData[int(ESRootWord[ESRootWord.rindex('-')+1:])-1]['NamedEntityTag']
					EONET = EOWData[int(EORootWord[EORootWord.rindex('-')+1:])-1]['NamedEntityTag']
					"""
					#print('\n\n')

					#if (ESNET not in pattern['OSNET'] and 'O' not in pattern['OSNET']):
					#	print('%s (%s) is not in %s' % (extractedSubject, ESNET, pformat(pattern['OSNET'])))

					#if (EONET not in pattern['OONET'] and 'O' not in pattern['OONET']):
					#	print('%s (%s) is not in %s' % (extractedObject, EONET, pformat(pattern['OONET'])))

					#if (EONET not in pattern['OONET'] and 'O' not in pattern['OONET']):
					#	continue
						#print_n_flush('IRRELEVANT: ')

					#print("\n\nIN %s\n(%s, %s, %s)" % (sentence, foundSubject,predicate,foundObject))
					#print('"%d", "%s", "%s", "%s","%s"' % (j, extractedSubject, predicate, extractedObject, pattern['hash']))
					#match = Match(extractedSubject, extractedObject, predicate, pattern['hash'], sourceURL, sentence)
					#pprint(labeledSubjectPath)
					
					if (extractedSubject, extractedObject) in pattern['sourcePairs']:
						trivialMatches += 1
						print('"%d", "%s", "%s", "%s","%s"' % (j, extractedSubject, predicate, extractedObject, pattern['hash']))
					#pprint(labeledObjectPath)
					#pprint(patternG.edges(data=True))
					#pprint(sentenceG.edges(data=True))
	if trivialMatches > 0:
		print('Trivial matches: %d' % (trivialMatches))
		
if __name__ == '__main__':

	# Open the Wikipedia dump through wikidump 
	wikipediaDump = wikiModel.Dump(	cfg['wikidumppath'],
									False,False)

	# Instantiate the English Wikipedia worder
	propertyWorder = EnglishWikipediaModule()

	language = propertyWorder.getLanguage()
	
	useCached = True
	if useCached:
		patterns = pickleLoad('patterns.obj')				
	else:
		patterns = fetchPatterns()
		pickleDump(patterns,'patterns.obj')
	print('>')
	"""
	k = len(patterns)
	for i, pattern in enumerate(patterns, 1):

		pattern['OSNET'] = set()
		pattern['OONET'] = set()
		

		l = len(pattern['sourcePairs'])
		for j, (originalSubject, originalObject) in enumerate(pattern['sourcePairs'], 1):
		
			try:
				(OSRootWord, OSW, OSG, originalSubject, OSWData) = annotateText(originalSubject, True)
				(OORootWord, OOW, OOG, originalObject, OOWData) = annotateText(originalObject, True)
			except AnnotationError:
				continue
		
			OSINDEX = int(OSRootWord[OSRootWord.rindex('-')+1:])-1
			OOINDEX = int(OORootWord[OORootWord.rindex('-')+1:])-1
		
			pattern['OSNET'].add(OSWData[OSINDEX]['NamedEntityTag'])
			pattern['OONET'].add(OOWData[OOINDEX]['NamedEntityTag'])
			#print('\t%d/%d' % (j,l))
			
		print('%d/%d' % (i,k))
			
	pickleDump(patterns,'patterns.obj')
	"""
	from time import sleep
	print('Now giving you 5 seconds to clear the screen...')
	print('\n')
	sleep(5)
	
	clear_screen()
	checkLog = False

 	#single text matching
	
	import codecs
	with codecs.open('sentencesSample.txt', encoding='utf-8') as f:	
		patternMatcher(f.readlines(), patterns, propertyWorder, '', presplit=True)
	 	
	exit()
	
	articles = open(cfg['articletitleslistfile'])
	currentArticle = 0

	# Debug
	#articles = ['Los_Angeles']
	
	for line in articles:
		title = line.replace('\n','')
		
		subjectIRI = expandIRI('dbpedia:' + title)
		subjectTriples = fetchSubjectTriples(subjectIRI, language, False, False)

		# End of DBPedia get triples
		#print 'OK'

		sourceWiki = language;

		# Obtain a pattern graph for the subject
		primaryTitleLabels = getValuesForPredicate(subjectTriples, 'rdfs:label')

		# We are pretty sure right now is a singleton 
		# (i.e. there is one triple for predicate rdfs:label)
		try:
			assert(len(primaryTitleLabels) == 1)
		except:
			message = "Could not find a primary label for " + title
			logging.warning(message)
			continue
		
		titleLabel = primaryTitleLabels.pop()

		# We do this instead
		try:
			text = wikipediaDump.get_page_contents_by_title(unidecode(titleLabel)).decode('utf-8')
		except KeyError:
			continue


		# Expand relevant templates
		text = expandTemplates(text, propertyWorder)
		# End of templates expansion

		# Remove wiki markup
		# Preliminary wiki markup cleanup
		text = WikiExtractor.clean(text)
		# Final wiki markup cleanup (turning text into a list of section titles and paragraphs)
		text = WikiExtractor.compact(text)
	
		text = u' '.join(text)

		""" Account for a bug in the PunktSentenceTokenizer when handling
		 	sentence-ending marks followed by a double quote mark """
	
		text = text.replace('?"', '? "')
		text = text.replace('!"', '! "')
		text = text.replace('."', '. "')
		
		processNext = False
		counter = 0
		
		sourceURL = 'http://%s.wikipedia.org/wiki/%s' % (sourceWiki, title)
		
		while not processNext:
			try: 
				processNext = False
				patternMatcher(text, patterns, propertyWorder, sourceURL)
				counter +=1
				currentArticle += 1
				processNext = True
			except (TimeoutError, BadStatusLine, URLError):
				if counter > 5:
					print('Ok, giving up and hoping %d articles are enough', currentArticle)
					break
				print_n_flush('It looks like your connection is down, trying again in 60 seconds...')
				sleep(60)

				continue
			except KeyboardInterrupt:
				if checkLog:
					print('Something went wrong, please check your error log.')
				print >>sys.stderr, "Bye."
				exit()
		
		if MAX_ARTICLES_TO_PARSE > 0 and currentArticle == MAX_ARTICLES_TO_PARSE:
			break
			
	if checkLog:
		print('Something went wrong, please check your error log.')
