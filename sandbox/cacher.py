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
from jsonrpc import RPCInternalError
from nltk.tokenize import sent_tokenize
from time import strftime
from jsonrpclib.jsonrpc import ProtocolError

# Debug
from pprint import pprint

def patternHarvester(title, propertyWorder, wikipediaDump, nlp, notWorded, tripleMatchCounter, savedPatternGraphs):	
	language = propertyWorder.getLanguage()
	
	print('Working on `' + title + '`')
 
	# Get triples from DBPedia
	print_n_flush('Querying DBPedia...')

	iri = '<' + namespaces['dbpedia'] + title + '>'
	dbpediaData = fetchSubjectTriples(iri,language, excludeRawTriples=False)
		
	# End of DBPedia get triples
	print 'OK'
	
	sourceWiki = language;
	
	# Obtain a pattern graph for the subject
	titleLabelSingleton = getPredicateValues(dbpediaData, 'rdfs:label')


	# We are pretty sure right now extendendSubjectLabels is a singleton (i.e. there is one triple for predicate rdfs:label)
	try:
		assert(len(titleLabelSingleton) == 1)
	except:
		message = "Could not find a label for " + title
		print(message)
		logging.warning(message)
		return
	titleLabel = iter(titleLabelSingleton).next() 

	subjectLabels = set({titleLabel})	
	subjectLabels |= otherNames(iri,language)

	resourceTypes = getPredicateLabels(dbpediaData, 'rdf:type')

	wordedTypeLabels = set(propertyWorder.getCapitalizedWordedClassLabel(typeLabel) for typeLabel in resourceTypes)
	wordedTypeLabels |= set(propertyWorder.getUncapitalizedWordedClassLabel(typeLabel) for typeLabel in resourceTypes)
	subjectLabels |= wordedTypeLabels

	subjectPatterns = dict()

	for label in subjectLabels:
		try:
			(rootWord, labelList, labelPattern) = wordingPattern(label,nlp)
		except RootWordUnidentifiable:
			continue
		subjectPatterns[label] = (rootWord, labelList, labelPattern)
	
	wordedTriples = list()
	wordingCounter = dict()
	
	# Compute and generate pattern graphs for object values
	for triple in dbpediaData:
		# Debug
		#break
		if triple['p']['value'] in ignored:
			continue
		try:
			triple['wording'] = getCommonWording(triple, propertyWorder)
		except CommonWordingNotFound:
			if triple['p']['value'] not in notWorded:
				notWorded[triple['p']['value']] = list()
			notWorded[triple['p']['value']].append(triple)
			continue

		try:

			(triple['wordingrootword'], triple['wordinglist'], triple['wordingpattern']) = wordingPattern(triple['wording'],nlp)
		except RootWordUnidentifiable:
			continue
			
		wordedTriples.append(triple)


	# Retrieve Wikipedia article
	print_n_flush('Retrieving article from Wikipedia...')
	
	# We don't do this anymore
	# text = getCurrentWikiArticleText(sourceWiki, title)
	# We do this instead
	text = wikipediaDump.get_page_contents_by_title(unidecode(titleLabel)).decode('utf-8')

	# End of Wikipedia article retrieving
	print 'OK'

	# Expand relevant templates
	print_n_flush('Expanding relevant templates...')
	text = expandTemplates(text, propertyWorder)
	# End of templates expansion
	print 'OK'

	# Remove wiki markup
	print_n_flush('Getting rid of wiki markup...')
	
	# Preliminary wiki markup cleanup
	text = WikiExtractor.clean(text)
	# Final wiki markup cleanup (turning text into a list of section titles and paragraphs)
	text = WikiExtractor.compact(text)

	# End of wiki markup cleaning
	print 'OK'

	i = 0

	for paragraph in text:
		# Debug
		#print(paragraph)
		#continue
		
		""" Account for a bug in the PunktSentenceTokenizer when handling sentence-ending marks followed by a double quote mark """
		paragraph = paragraph.replace('?"', '? "').replace('!"', '! "').replace('."', '. "')
		sentences = tokenize_sentence(paragraph)
		for sentence in sentences:
			sentence = propertyWorder.adjustText(sentence)

			if sentence == 'Q':
				continue

			i += 1

			if len(sentence) >= 1022:
				"""A bug in pexpect produces \x07 chars and messes up everything when input is >= 1023 chars"""
				logging.warning('Encountered sentences with more than 1021 chars, skipping: ' + sentence)
				continue

			# Get the graph for this sentence
			#print_n_flush('PS')

			# Parse the sentence through the Stanford NLP Core Tools
			try:
				result = nlp.parse(sentence)
			except ProtocolError as e :
				errorCode = e.message[0]
				errorMessage = e.message[1]
				#TODO: Find the source of this invalid bytes (might be just DBPedia's culprit)
				if errorCode == -32603 and 'UnicodeDecodeError' in errorMessage:
					checkLog = True
					""" Something in JSONRPClib makes invalid JSON even though strings are correctly UTF8 encoded"""
					logging.warning('The JSONRPCServer had problems with the following sentence: ' + sentence)
					logging.exception(str(e))
				elif errorCode == -32603 and 'TimeoutError' in errorMessage:
					continue
				else:
					raise e
				continue
			except InvalidSentence as e:
				logging.warning('Sentence would quit SCNLP tools and was not sent: ' + wording)
				logging.exception(str(e))
				continue
			

if __name__ == '__main__':

	logging.basicConfig(filename=os.path.join(cfg['home'],'cacher.log'), level=logging.DEBUG, format=cfg['logtimestampformat'])


	# Open the Wikipedia dump through wikidump 
	wikipediaDump = wikiModel.Dump('/Volumes/Data/wikidump/enwiki-20130304-pages-articles.xml',False,False)

	# Instantiate the English Wikipedia worder
	propertyWorder = EnglishWikipediaModule()

	# Establish RPC connection to the Stanford Core NLP Tools Server
	nlp = StanfordCoreNLP()

	# List of predicates without a wording
	notWorded = dict()

	# Maintain a list of matches so to have sequential names for patterns graphs for the same property
	tripleMatchCounter = dict()

	savedPatternGraphs = dict()

	clear_screen()
	articles = open('cities.txt')
	currentArticle = 0
	checkLog = False
	# Debug
	#articles = ['Hamburg']
	for line in articles:
		title = line.replace('\n','')
	
		print_n_flush('\n' + unicode(currentArticle) + ':')
	
		processNext = False
		counter = 0
		while not processNext:
			try: 
				processNext = False
				patternHarvester(title, propertyWorder, wikipediaDump, nlp, notWorded, tripleMatchCounter, savedPatternGraphs)
				counter +=1
				currentArticle += 1
				processNext = True
			except (TimeoutError, BadStatusLine, URLError):
				if counter > 5:
					print('Ok, giving up and hoping ' + currentArticle + ' articles are enough')
					break
				print_n_flush('It looks like your connection is down, trying again in 60 seconds...')
				sleep(60)

				continue
			except EOFError:
				message = "Pickling problem with this resource's DBPedia query results: " + article
				print(message)
				log.warning(message)
				continue
			except KeyboardInterrupt:
				if checkLog:
					print('Something went wrong, please check your error log.')
				print >>sys.stderr, "Bye."

				exit()
		
		#if currentArticle == 1:
			#break

	if checkLog:
		print('Something went wrong, please check your error log.')

