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
import hashlib
from database import * 

class Pattern(object):

	def __init__(self, pydot, predicate, entities, wikipediaArticle, subjectWording, objectWording, sentence):
		# Hashes for patterns are the md5 hash of the DOT representation string
		# for their associated graphs
		self.hash = hashlib.sha224(pydot).hexdigest()
		
		self.pydot = pydot
		self.entities = entities
		self.predicate = predicate
		
		patternSource = PatternSource(self.hash, wikipediaArticle, subjectWording, objectWording, sentence)
		
		storePattern(self, patternSource)
		
	def __str__(self):
		return self.hash	
	
class PatternSource(object):

	def __init__(self, patternHash, wikipediaArticle, subjectWording, objectWording, sentence):
		self.patternHash = patternHash
		self.wikipediaArticle = wikipediaArticle
		self.sentence = sentence
		self.subjectWording = subjectWording
		self.objectWording = objectWording
		
class Match(object):

	def __init__(self, subjectWording, objectWording, predicate, matchedPatternHash, sourceURL,  sentence):
		
		triple = '(%s,%s,%s)' % (subjectWording, predicate, objectWording)
		x = triple.encode(encoding='UTF-8')
		
		self.hash = hashlib.sha224(x).hexdigest()

		self.subjectWording = subjectWording
		self.objectWording = objectWording
		self.matchedPatternHash = matchedPatternHash
		self.predicate = predicate
		
		matchSource = MatchSource(self.hash, sourceURL, sentence)

		storeMatch(self, matchSource)
		
	def __str__(self):
		return self.hash
		
class MatchSource(object):

	def __init__(self, matchHash, sourceURL, sentence):
		self.matchHash = matchHash
		self.sourceURL = sourceURL
		self.sentence = sentence
