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
from pprint import pformat

# First item to process in list of articles
startFrom = 0

# Debug
from pprint import pprint, pformat

def patternHarvester(title, propertyWorder, wikipediaDump):	

	language = propertyWorder.getLanguage()
	sourceWiki = language;

	print('Working on `%s`' % title)

	############################################################################ 
	# 						Fetch triples for subject				   		   #
	
	print_n_flush('Querying DBPedia...')

	subjectIRI = expandIRI('dbpedia:' + title)
	
	subjectTriples = fetchSubjectTriples(subjectIRI, language, False, False)

	print 'OK'
	
	# 						End of "Fetch triples for subject"				   #
	############################################################################
	
	# Obtain title for the article (i.e. primary subject name)
	primaryTitleLabels = getValuesForPredicate(subjectTriples, 'rdfs:label')

	# We are pretty sure right now is a singleton 
	# (i.e. there is one triple for predicate rdfs:label)
	try:
		assert(len(primaryTitleLabels) == 1)
	except:
		projectedTitle = title.replace('_',' ')
		primaryTitleLabels = {unicode(projectedTitle)}
		message = "Could not find a primary label for %s, will try %s" % (title, projectedTitle)
		print(message)
		
	titleLabel = primaryTitleLabels.pop()

	############################################################################ 
	# 						Retrieve article for subject					   #
	print_n_flush('Retrieving article from Wikipedia...')
	
	# We don't do this anymore
	# article = getCurrentWikiArticleText(sourceWiki, title)

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
	# 						End of "Retrieve article for subject"
	############################################################################

	subjectWordings = set()
	subjectWordings.add(titleLabel)	
	
	# Retrieve secondary names (obtained from redirects to the primary article)
	# and add them as subject labels
	subjectWordings |= otherLabels(subjectIRI, language)
	
	# Filter and get the labels for the classes the subject is an instance of 
	# (e.g. Los Angeles would have "city" as a label to an object for a 
	# rdf:type triple)
	subjectClasses = getLabelsForPredicate(subjectTriples, 'rdf:type')

	wordedClassLabels = set()

	for classLabel in subjectClasses:
		captlzd, uncptlzd = propertyWorder.getClassLabelWording(classLabel)
		wordedClassLabels.add(uncptlzd)
		wordedClassLabels.add(captlzd)
			
	subjectWordings |= wordedClassLabels

	### Compute and annotate wordings for triple objects

	annotatedSubjectWordings = list()

	# Cycle through all wordings for the subject and get an annotation 
	# for each one
	for subjectWording in subjectWordings:
		try:
			(root, words, graph) = annotateText(subjectWording)
		except AnnotationError:
			continue
			
		annotatedSubjectWordings.append((subjectWording, (root, words, graph)))
	
	
	### Compute and annotate wordings for objects in each triple
	print_n_flush('Finding and annotating wordings for triple objects...')

	annotatedObjectWordings = list()

	predicateOccurrences = dict()
	
	for triple in subjectTriples:
		predicate = triple['p']['value']
		
		if predicate in ignored:
			continue
			
		if predicate not in predicateOccurrences:
			predicateOccurrences[predicate] = set()
					
		try:
			objectWording = getCommonWording(triple, propertyWorder)
		except CommonWordingNotFound:
			# TODO: Find out if any important data types are left out
			"""
			if triple['p']['value'] not in notWorded:
				notWorded[triple['p']['value']] = list()
			notWorded[triple['p']['value']].append(triple)

			pprint(triple['p']['value'] + '::' + triple['o']['value'])
			pprint(triple)
			"""
			continue

		try:
			(root, words, graph) = annotateText(objectWording)
		except AnnotationError:
			continue
		
		annotatedObjectWordings.append((objectWording, (root, words, graph, predicate)))
	
	### END of templates expansion
	print 'OK'


	### Expand relevant templates in the Wikipedia article
	print_n_flush('Expanding relevant templates...')
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

	# Sentence counter
	i = 0
	j = -1
	
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

			# Statistics
			for ow, (owRootWord, owWords, owGraph, predicate) in annotatedObjectWordings:
				if ow in sentence:
					predicateOccurrences[predicate].add(ow)

			i += 1

			# Get the graph for this sentence
			print_n_flush('PS')

			# Parse the sentence through the Stanford NLP Core Tools
			try:
				(sentenceR, sentenceW, sentenceG, sentence, sentenceWData) = annotateText(sentence, True)
			except AnnotationError:
				continue
			
			legalNodeIndices = map(lambda x: int(x[x.rindex("-")+1:]), sentenceG.nodes())
			
			rootNode = 'ROOT-0'
			
			# From here on, the initials "sw" refer to "subject wording"
			
			for sw, (swRootWord, swWords, swGraph) in annotatedSubjectWordings:
				
				try:
					swRootWordIndex = matchWording(sentence, sentenceW, sentenceG, legalNodeIndices, sentenceWData, sw, swWords, swGraph, swRootWord)
				except ValueError as e:
					"""No match found for wording in sentence"""
					continue
					
				subjectTarget = swRootWord + '-' + unicode(swRootWordIndex)
												
 				# Compute and generate subgraph for shortest path to Subject 
				# s1 will be the nodes from root to subject
				try:
					s1 = set(shortestPathFromRoot(sentence, sentenceG, subjectTarget))
				except ShortestPathError:
					continue
				
				# From here on, the initials "ow" refer to "object wording"
				
				# Compute and generate subgraph for shortest path to Object
				# s2 is the set of nodes from root to object
				for ow, (owRootWord, owWords, owGraph, predicate) in annotatedObjectWordings:
					
					try:
						owRootWordIndex = matchWording(sentence, sentenceW, sentenceG, legalNodeIndices, sentenceWData, ow, owWords, owGraph, owRootWord)

					except ValueError as e:
						"""No match found for wording in sentence"""
						continue
					
					objectTarget = owRootWord + '-' + unicode(owRootWordIndex)

					if objectTarget == subjectTarget:
						""" No use for this kind of pattern """
						continue

					try: 
						s2 = set(shortestPathFromRoot(sentence, sentenceG, objectTarget))
					except ShortestPathError:
						continue
					
					# At this point, we definitely have a pattern
					
					# Nodes in the spanning tree comprising solely the shortest
					# paths to the subject and to the object
					s = s1 | s2

					# S is the aforementioned spanning tree 
					S = nx.DiGraph(sentenceG.subgraph(s), name=predicate)
	
					anonRoot = unicode(cfg['roottag'] + '-0')
					anonSubject = unicode(cfg['subjecttag'] + '-' + unicode(swRootWordIndex))					
					anonObject = unicode(cfg['objecttag']  + '-' + unicode(owRootWordIndex))

					renamings = dict()

					renamings[rootNode] = anonRoot
					renamings[subjectTarget] = anonSubject
					renamings[objectTarget] = anonObject

					entities = list()	
					numerals = 0				
					
					try:
						for node in S.nodes():
							if node not in renamings.keys():
								if propertyWorder.partOfProperNoun(node):
									""" The word may refer to an entity, in this 
									 	case let's abstract from the word and save a 	
										relation for this pattern"""
									index = int(node[node.rindex('-')+1:])
														
									anonEntity = '%s%05d-%d' % (cfg['entitytagprefix'], len(entities), index)
								
									renamings[node] = anonEntity
								
									entityWording = associatedWording(sentence, node, sentenceG, sentenceWData, allowNestedWordingMatch=True)	

									entities.append((entityWording, getClasses(entityWording, language)))
									
								elif isNumeric(node):
									index = int(node[node.rindex('-')+1:])

									anonNumeral = '%s%05d-%d' % (cfg['numerictagprefix'], numerals, index)
									numerals += 1
									renamings[node] = anonNumeral

					except AnnotationError:
						continue
						
					# First anonymize subject, object and entities
					S = nx.relabel_nodes(S, renamings)
					
					# Remove indices as well
					indexlessNodes = map(lambda word: word[0:word.rindex("-")], S.nodes()) 
					
					S = nx.relabel_nodes(S, dict(zip(S.nodes(), indexlessNodes)))

					if '' in S.nodes():
						"""	A bug in either the SCNLP or the python wrapper makes empty nodes out of
						 	schwas and other unicode chars that might be used as a diacritic"""
						# TODO: Find a fix for this
						message = 'Invalid dependencies for this sentence: ' + sentence
						logging.warning(message)
						print(message)
						continue
			
					# DOT representation of the graph 
					pydotS = nx.to_pydot(S).to_string().encode(encoding='UTF-8', errors='strict')

					pattern = Pattern(pydotS, predicate, entities, title, sw, ow, sentence)
					
					try:
						saveGraph(S, pattern.hash)
					except (TypeError, UnicodeEncodeError):
						# TODO: Fix this "TypeError: coercing to 
						# Unicode: need string or buffer, NoneType found" error
						# also : "UnicodeEncodeError: 'ascii' codec can't encode character"
						checkLog = True
						logging.warning('A graph could not be saved: '
										'Sentence: ' + sentence +
										'Nodes: ' + str(S.nodes()) +
										'Edges: ' + str(S.edges(data=True)))
						pass
						
	storePredicateOccurrences(title, predicateOccurrences)


if __name__ == '__main__':

	logging.basicConfig(filename=os.path.join(cfg['home'],'pairses.log'), 
						level=logging.DEBUG, format=cfg['logtimestampformat'])

	# Open the Wikipedia dump through wikidump 
	wikipediaDump = wikiModel.Dump(cfg['wikidumppath'], False, False)

	# Instantiate the English Wikipedia worder
	propertyWorder = EnglishWikipediaModule()

	clear_screen()
	articles = open(cfg['articletitleslistfile'])
	
	currentArticle = -1
	checkLog = False
	# Debug
	#articles = ['New_Hampton,_Iowa']

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
				patternHarvester(title, propertyWorder, wikipediaDump)
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
		
		if currentArticle == 2: break

	if checkLog:
		print('Something went wrong, please check your error log.')
