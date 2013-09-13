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

import networkx as nx
import pygraphviz as pgv
from classes import *
from graphs import *
from configuration import *
from common import *
from dbpedia import *
from wording import isNumeric
import os, shutil, logging
from jsonrpclib.jsonrpc import ProtocolError
from pprint import pformat

def annotateText(text, completeSentence = False):
	"""Parses text to return its root word, a list of its word tokens and a dependency graph"""
	
	try:
		results = nlp.parse(text)
	except ProtocolError as e :

		#TODO: Find the source of this invalid bytes (might be just DBPedia's culprit)
		errorCode = e.message[0]
		errorMessage = e.message[1]

		if errorCode == -32603:
			checkLog = True
			if 'UnicodeDecodeError' in errorMessage:
				""" Something in JSONRPClib makes invalid JSON even though
				 	strings are correctly UTF8 encoded"""
				logging.warning('The JSONRPCServer had problems with the following sentence: ' + text)
				
			elif 'TimeoutError' in errorMessage:
				logging.warning('The JSONRPCServer timed out with the following sentence: ' + text)	
			else:
				raise e
			logging.exception(e)
			raise AnnotationError()	
		else:
			raise e

	except InvalidSentence as e:
		checkLog = True
		logging.warning('Sentence would quit SCNLP tools and was not sent: ' + text)
		logging.exception(e)
		raise AnnotationError()	

	try: 
		sentenceAnnotations = results['sentences'][0]
	except IndexError as e:
		checkLog = True
		logging.exception(e)
		raise AnnotationError()
		
	sentence = sentenceAnnotations['text']	
		
	if completeSentence:
		dependencyTuples = sentenceAnnotations['originaldependencies']
	else:
		dependencyTuples = sentenceAnnotations['dependencies']
		
	# Graph for dependencies
	sentenceG = nx.DiGraph()

	if len(dependencyTuples) < 1:
		"""A bug in the SCNLP tools prevents dependencies to be relayed when a sentence is 
			a single word enclosed by parenthesis (e.g. "(US)")
		"""
		raise AnnotationError()
	
	rootWord = None
	
	# Cycle through all dependencies for this pattern
	for t in dependencyTuples:
		reltag, tail, head = t
	
		head = fixNodeName(head)
		tail = fixNodeName(tail)
	
		if (reltag == 'root'):
			rootWord = head
		
		sentenceG.add_node(head)
		sentenceG.add_node(tail)
		sentenceG.add_edge(tail, head, label=reltag)		
	
	if rootWord is None:
		raise AnnotationError()
	
	words = list()
	if completeSentence:
		wordsData = list()
	
	rawWords = sentenceAnnotations['words']
	
	for rawWord in rawWords:
		if rawWord is not None:
			words.append(rawWord[0])
			if completeSentence:
				wordsData.append(rawWord[1])

	if completeSentence:
		return (rootWord, words, sentenceG, sentence, wordsData)
	else:
		return (rootWord, words, sentenceG)

def associatedWording(sentence, numberedRootWord, sentenceG, sentenceWData, allowNestedWordingMatch=False):
	"""Given a numbered root word, returns its wording indices for its first and its last word"""
	# These are the only relations that must be considered when grouping a wording's pieces
	compounding = ['nn', 'num', 'number', 'amod']
	
	returnRootWordOnly = False
	
	# First we check whether the root word is part of a compound
	for tail, head, data in sentenceG.in_edges_iter(numberedRootWord, data=True):
		if data['label'] in compounding:
			if not allowNestedWordingMatch:
				raise NestedWordingMatch()
			else: 
				returnRootWordOnly = True
				#print("%s" % (numberedRootWord))
				#numberedRootWord = tail
				#print("%s" % (numberedRootWord))
				break

	if returnRootWordOnly:
		index = int(numberedRootWord[numberedRootWord.rindex("-")+1:])
		firstWord = index
		lastWord = index
	else:
		# From the sentence graph we only take the subgraph made by the root word and its successors
		targetNodes = sentenceG.successors(numberedRootWord)
		targetNodes.append(numberedRootWord)

		wordingGraph = nx.DiGraph(sentenceG.subgraph(targetNodes))

		# Here we clean up and remove the nodes outside the aforementioned relations
		for tail, head, data in wordingGraph.edges_iter(numberedRootWord, data=True):
			if data['label'] not in compounding and tail != head:
				wordingGraph.remove_node(head)

		# Now we must not consider any other unconnected subgraphs
		wordingNodes = wordingGraph.successors(numberedRootWord)
		wordingNodes.append(numberedRootWord)
	
		# The remaining nodes make up the wording, we now need their indices
		# (Did I mention I always get excited when I get to use a lambda function?)
		indices = map(lambda word: int(word[word.rindex("-")+1:]), wordingNodes)
	
		firstWord, lastWord = min(indices)-1, max(indices)-1
	
	try:
		firstChar = int(sentenceWData[firstWord]['CharacterOffsetBegin'])
		lastChar = int(sentenceWData[lastWord]['CharacterOffsetEnd'])
	except KeyError:
		"""	Deal with a problem due to tokens with square brackets
			that make the SCNLP wrapper incorrectly parse the results"""
		#TODO: Fix the SCNLP wrapper to avoid this behaviour
		raise AnnotationError()
		
	wording = sentence[firstChar:lastChar]
	
	return wording
		
def matchWording(sentence, sentenceW, sentenceG, legalNodeIndices, sentenceWData, wording,  wordingW, wordingG, wordingRootWord):
	"""Finds the root word's number for an exactly matching wording in the sentence"""
	"""Raises ValueError when the wording is not found in the sentence"""

	# Find if and where does the root word appear in the sentence	
	rootWordIndices = [int(x[x.rindex('-')+1:]) for x in sentenceG.nodes() if x[:x.rindex('-')] == wordingRootWord]

	# If the list is empty, no match was found
	if not rootWordIndices:
		raise ValueError

	for rootWordIndex in rootWordIndices:	
		# It is not always sure that the SNLP tools find a relation 
		# between the subject's root word and another in the sentence
		if rootWordIndex not in legalNodeIndices:
			continue
			
		numberedCandidateRootWord = wordingRootWord + '-' + unicode(rootWordIndex)		
		
		try:
			matchedWording = associatedWording(sentence, numberedCandidateRootWord, sentenceG, sentenceWData)
		except (NestedWordingMatch, AnnotationError):
			continue
								
		if matchedWording == wording:
			return rootWordIndex
	
	raise ValueError

def shortestPathFromRoot(sentence, sentenceG, targetNode):
	
	rootNode = cfg['scnlprootnode']
		
	try:
		nodes = nx.shortest_path(sentenceG, source=rootNode, target=targetNode)
		
	except nx.NetworkXNoPath as e:
		"""	Account for a bug in the SCNLP tools generating 		
			dependencies such that a bracketed expression obstructs
			the correct dependency computation for its following 		
			text
		"""

		H = sentenceG.to_undirected()					
		if nx.number_connected_components(H) > 1:
			message = ('Invalid dependencies for this sentence: ', 
						sentence)
			logging.warning(message)
			raise ShortestPathError()
		else:
			raise e

	except nx.NetworkXError as e:
		# A nasty bug in the Stanford NLP Core Tools sometimes makes
		# them not relay a ROOT node
		checkLog = True
		logging.warning('The SCNLP Tools failed to parse correctly this sentence: ' + sentence)
		logging.exception(e)
		raise ShortestPathError()

	sp = nodes
	
	return sp

def compatibleNodes(head, edge, sentence, sentenceG, sentenceWData, (patternEdge, patternHead), patternEntities, numericObject, propertyWorder):

		language = propertyWorder.getLanguage()

		subjectTag = cfg['subjecttag']	
		objectTag = cfg['objecttag']
		entityTagPrefix = cfg['entitytagprefix']
		numericTagPrefix = cfg['numerictagprefix']
		
		if edge != patternEdge:

			return False
			
		elif patternHead == subjectTag:
			return True
			
		elif patternHead == objectTag:
			return numericObject == isNumeric(head)
		
		elif patternHead.startswith(numericTagPrefix):
			return isNumeric(head)
		
		elif patternHead.startswith(entityTagPrefix):
			if not propertyWorder.partOfProperNoun(head):
				return False
				
			patternEntityNo = int(patternHead[len(entityTagPrefix):])

			try:
				# Def. "isotopic" as in "in the same position"
				isotopicEntityWording = associatedWording(sentence, head, sentenceG, sentenceWData, allowNestedWordingMatch=True)

			except AnnotationError:
				return False
				
			# Retrieve label for head
			isotopicEntityClasses = set(getClasses(isotopicEntityWording, language))
			
			return not empty(isotopicEntityClasses.intersection(patternEntities[patternEntityNo][1]))
			
		else:
			unnumberedHead = head[:head.rindex("-")]

			return patternHead == unnumberedHead

def pathDestinations(sentence, sentenceG, sentenceWData, labeledPath, patternEntities, numericObject, propertyWorder):

	language = propertyWorder.getLanguage()

	rootNode = cfg['scnlprootnode']

	#labeledPath items have the form (edge, node)
	
	destinations = []

	level = 0
	stack = []
 	stack.append([rootNode])

	encounteredLoop = False
	
	while level >= 0:

		tail = stack[level].pop()

		level += 1
		stack.append(list())
 	
		for _, head, data in sentenceG.out_edges(tail, data=True):
	
			for tails in stack:
				if head in tails:
					encounteredLoop = True
					break
					
			if encounteredLoop:
				encounteredLoop = False
				continue
			
			edge = data['label']		


			if compatibleNodes(head, edge, sentence, sentenceG, sentenceWData, labeledPath[level-1], patternEntities, numericObject, propertyWorder):

				if level == len(labeledPath):
					# Reached end of path
					destinations.append(head)
				else:
					# We need to go deeper
					stack[level].append(head)

	
		while empty(stack[level]):
			stack.pop()
 			level -= 1
			if level < 0:
				break
			
	return destinations

def prettyPrintPatternsGallery(patternGraphs, predicatesPerPage=10):
	"""Generates a HTML gallery for visual presentation of pattern graphs"""
	resourcesDir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources'))

	indexFile = cfg['prettypatternsgallery_index']

	outputDir = os.path.dirname(indexFile)

	# First of all copy the convenience dir with all supporting files (js, etc.)
	targetResourcesDir = os.path.join(outputDir, 'resources')

	shutil.rmtree(targetResourcesDir,ignore_errors = True)
	shutil.copytree(resourcesDir, targetResourcesDir)

	# Fetch header html
	headerFile = os.path.join(resourcesDir, 'graphsHeader.html')
	with open(headerFile,'r') as header:
		headerhtml = ' '.join(header.readlines()[:])

	# Fetch footer html
	footerFile = os.path.join(resourcesDir, 'graphsFooter.html')
	with open(footerFile,'r') as footer:
		footerhtml = ' '.join(footer.readlines()[:])

	indexhref = os.path.relpath(indexFile, os.path.dirname(indexFile))

	def createNextPage(j):
		pageHeader = '%s<h3>Page #%d</h3><h3><a href="%s">Back to index</a></h3>' % (headerhtml, j, indexhref)
		outputFile = cfg['prettypatternsgallery_name'] % (j)

		output = open(outputFile, 'w')
		output.write(pageHeader)
		return output

	def finishCurrentPage(output):
		output.write(footerhtml)
		output.close()

	totalPatterns = 0

	i = 1
	page = 0

	output = createNextPage(page)
	
	for predicate, patterns in sorted(patternGraphs.iteritems()):
		
		predicateTotalPatterns = len(patterns)
		totalPatterns += predicateTotalPatterns
		
		html = unicode()
		html = '<div class="%s"><div class="%s">%s</div><div class="%s">%d patterns</div>' % ('predicate', 'uri', predicate,'predicateTotalPatterns',predicateTotalPatterns)
		html += '<div class="%s">' % ('patternGraphs')	
		

		for pattern in sorted(patterns, key= lambda pattern: pattern['hash']):

			patternFilename = pattern['hash'] + '.png'
			patternPath = os.path.join(outputDir, patternFilename)
			thumbFilename = pattern['hash'] + '_thumb.png'
			thumbPath = os.path.join(outputDir, thumbFilename)
			
			# HTML chars
			for key, value in pattern.iteritems():
				if (type(value) is unicode) or (type(value) is str):
					pattern[key] = value.replace("\"","'")
			
			caption = '%s __NEWLINE__ __NEWLINE__ Hash: %s Subject: %s __NEWLINE__ Object: %s __NEWLINE__ Sentence: %s' % (predicate, pattern['hash'], pattern['subject'], pattern['object'], pattern['sentence'])


			for key, (entity, entityType) in enumerate(pattern['entities']):
				caption += '__NEWLINE__ __NEWLINE__Entity %05d: %s' % (key,entity)
				caption += '__NEWLINE__Info on entity: %s' % (pformat(entityType))
			
			html += '<a class="fancybox" rel="%s" href="%s" title="%s">' % (predicate, patternFilename, caption)
			html += '<img src="%s">' % (thumbFilename)
			html += '</a>'

		html += '</div>'
		html += '</div>'
		html = html.encode('ascii', 'xmlcharrefreplace')
		output.write(html)

		if iszero(i%predicatesPerPage):
			finishCurrentPage(output)
			page += 1
			output = createNextPage(page)

		i += 1

	finishCurrentPage(output)
	
	with open(indexFile, 'w') as output:	
		output.write(headerhtml)
		
		patternsInfoHtml = '<div class="patternsInfo">%s%d</div>' % ('Total patterns found: ', totalPatterns)
		output.write(patternsInfoHtml)		
		
		for k in range(0, page+1):
			filename = cfg['prettypatternsgallery_name'] % (k)
			# Locate paths relative to output dir
			href = os.path.relpath(filename, os.path.dirname(filename))
			output.write('<a href="%s">Page %d</a><br>' % (href,k))
		finishCurrentPage(output)

def prettyPrintMatchesGallery(matches):
	"""Generates a HTML gallery for visual presentation of matches"""

	reordered = dict()
	
	uniqueTriples = set()
	usedPatterns = set()
	
	maxTriplesPerPage = 200
	maxPatternsPerMatch = 5	
	
	print_n_flush('Now sorting matches...')
	
	for predicate, predicateMatches in sorted(matches.iteritems()):

		if predicate not in reordered:
			reordered[predicate] = dict()

		for match in predicateMatches:
			pprint(match)
			exit()
			foundTriple = (match['match']['subject'], predicate, match['match']['object'])
	
			uniqueTriples.add(foundTriple)
			
			pattern = (match['pattern']['subject'], match['pattern']['object'], match['pattern']['sentence'], match['match']['sentence'])
			usedPatterns.add(pattern[:3])

			if foundTriple not in reordered[predicate]:
				reordered[predicate][foundTriple] = list()

			reordered[predicate][foundTriple].append(pattern)

	print_n_flush('OK')

	resourcesDir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources'))

	indexFile = cfg['prettymatchesgallery_index']

	outputDir = os.path.dirname(indexFile)

	# First of all copy the convenience dir with all supporting files (js, etc.)
	targetResourcesDir = os.path.join(outputDir, 'resources')

	shutil.rmtree(targetResourcesDir,ignore_errors = True)
	shutil.copytree(resourcesDir, targetResourcesDir)

	# Fetch header html
	headerFile = os.path.join(resourcesDir, 'matchesHeader.html')
	with open(headerFile,'r') as header:
		headerhtml = ' '.join(header.readlines()[:])

	# Fetch footer html
	footerFile = os.path.join(resourcesDir, 'matchesFooter.html')
	with open(footerFile,'r') as footer:
		footerhtml = ' '.join(footer.readlines()[:])

	indexhref = os.path.relpath(indexFile, os.path.dirname(indexFile))

	pages = list()

	def createNextPage(predicate, pageNo, triplesTotal):
		pageHeader = '%s<h3>%s</h3><h3><a href="%s">Back to index</a></h3>' % (headerhtml,predicate,indexhref)
		outputFile = cfg['prettymatchesgallery_name'] % (filenameCompatibleString(predicate),pageNo)

		if (pageNo == 0):
			pages.append((predicate,triplesTotal))

		output = open(outputFile, 'w')
		output.write(pageHeader)
		return output

	def finishCurrentPage(output):
		output.write(footerhtml)
		output.close()

	for predicate, predicateTriples in sorted(reordered.iteritems()):
		print('Now working on %s' % (predicate) )
		
		i = 0
		output = createNextPage(predicate, 0, len(predicateTriples))
		html = unicode()

		for (s,p,o), allSources in sorted(predicateTriples.iteritems()):
			html += '<div class="%s">' % ('match')
			html += '<div class="triple">%s %s %s</div>' % (s,p,o)

			sources = allSources[:maxPatternsPerMatch]
			
			if len(sources) < len(allSources):
				html += '<div class="%s">%d %s</div>' % ('notshown', len(allSources)-maxPatternsPerMatch, 'more matching patterns not shown.')

			html += '<div class="%s">' % ('scrollmatchtable')

			html += '<table class="%s">' % ('matchtable')
			# Subject
			html += '<tr>'
			html += '<td class="%s">S</td>' % ('first')

			for source in sources:
				html += '<td class="%s">%s</td>' % ('column',source[0])

			html += '</tr>'
			
			# Object
			html += '<tr>'
			html += '<td class="%s">O</td>'  % ('first')
			for source in sources:
				html += '<td>%s</td>' % (source[1])	
					
			html += '</tr>'

			# Sentences
			html += '<tr>'
			html += '<td class="first bottom-left-angle"></td>'

			for source in sources:
				html += '<td>%s</td>' % (source[2])	

			html += '</tr>'


			# Matched sentences
			html += '<tr>'
			html += '<td class="first bottom-left-angle"></td>'
			
			for source in sources:
				html += '<td>%s</td>' % (source[3])

			html += '</tr>'

			html += '</table>'	
			html += '</div>'
			html += '</div>'
			i += 1
			if i%maxTriplesPerPage == 0:
				html = html.encode('ascii', 'xmlcharrefreplace')
				output.write(html)
				finishCurrentPage(output)
				output = createNextPage(predicate, i/maxTriplesPerPage, len(predicateTriples))
				html = unicode()

		html = html.encode('ascii', 'xmlcharrefreplace')
		output.write(html)

		finishCurrentPage(output)

	with open(indexFile, 'w') as output:	
		output.write(headerhtml)
		output.write('Total patterns used: %d<br>' % (len(usedPatterns)))
		output.write('Unique triples found: %d' % (len(uniqueTriples)))
		for predicate, triplesTotal in pages:
			output.write('<p><b>%s</b>, %d matches<br>' % (predicate, triplesTotal))
			
			for i in range((triplesTotal/maxTriplesPerPage)+1):
					# Locate paths relative to output dir
					filename = cfg['prettymatchesgallery_name'] % (filenameCompatibleString(predicate), i)
					href = os.path.relpath(filename, os.path.dirname(filename))
					output.write('<a href="%s">%s %d</a> <br>' % (href, 'Page', i))
			output.write('</p>')
			
		finishCurrentPage(output)