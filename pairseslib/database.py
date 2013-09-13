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

import sqlite3
from configuration import cfg
from wording import isNumeric
from json import dumps, loads
import networkx as nx
from graphs import pydotStringToDiGraph
from time import sleep

conn = None

def patternDictFactory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		
		if col[0] == 'pydot':
			d['graph'] = pydotStringToDiGraph(loads(row[idx]))
			d['pgraph'] = loads(row[idx])
		elif col[0] == 'objectIsNumeric':
			d['numericObject'] = bool(row[idx])
		elif col[0] == 'entities':
			d['entities'] = map(lambda (x,y): (x, set(y)), loads(row[idx]))
		else:
			d[col[0]] = row[idx]
	
		d['sourcePairs'] = fetchPatternSources(d['hash'])
	
	return d

def initDBConnection():
	global conn
	if not conn:
		conn = sqlite3.connect(cfg['databasepath'])
		
def storePattern(pattern, source):
	global conn
		
	initDBConnection()
	
	insertPatternQueryArgs = {  'h': pattern.hash,
								'pr': pattern.predicate,
								'pd': dumps(pattern.pydot),
								'e': dumps(pattern.entities),
								'oin': int(isNumeric(source.objectWording))
								
							 }
	
	insertPatternQuery = ('INSERT OR REPLACE INTO Patterns (hash, predicate, pydot, entities, objectIsNumeric) VALUES (:h, :pr, :pd, :e, :oin)')
	
	conn.execute(insertPatternQuery, insertPatternQueryArgs)
	
	insertSourceQueryArgs = { 'ph': source.patternHash, 
						'wa': source.wikipediaArticle,
						's': source.sentence,
						'sw': source.subjectWording,
						'ow': source.objectWording
					  }
	
	insertSourceQuery = ('INSERT OR REPLACE INTO PatternSources (pattern, wikipediaArticle, sentence, '
						 'subjectWording, objectWording) VALUES (:ph, :wa, :s, :sw, :ow)')
	
	conn.execute(insertSourceQuery, insertSourceQueryArgs)
	
	while True:
		try:
			conn.commit()
		except sqlite3.OperationalError:
			sleep(3)
			continue
		else:
			break
			
def storeMatch(match, source):
	global conn
		
	initDBConnection()
	
	insertMatchQueryArgs = {  	'h': match.hash,
								'mph': match.matchedPatternHash,
								'pr': match.predicate,
 								'sw': match.subjectWording,
								'ow': match.objectWording
							 }
	
	insertMatchQuery = ('INSERT OR REPLACE INTO Matches (hash, matchedPattern, predicate, subjectWording, objectWording) VALUES (:h, :mph, :pr, :sw, :ow)')
	
	conn.execute(insertMatchQuery, insertMatchQueryArgs)
	
	insertSourceQueryArgs = { 	'mh': source.matchHash, 
								'surl': source.sourceURL,
								's': source.sentence
							}
	
	insertSourceQuery = ('INSERT OR REPLACE INTO MatchSources (match, sourceURL, sentence) '
						 'VALUES (:mh, :surl, :s)')
	
	conn.execute(insertSourceQuery, insertSourceQueryArgs)
	
	while True:
		try:
			conn.commit()
		except sqlite3.OperationalError:
			sleep(3)
			continue
		else:
			break
			
def storePredicateOccurrences(wikipediaArticle, predicateOccurrences):
	global conn
		
	initDBConnection()
	
	args = [(wikipediaArticle, predicate, len(wordings)) for predicate, wordings in predicateOccurrences.items()]
	
	query = ('INSERT OR REPLACE INTO PredicateOccurrences (wikipediaArticle, predicate, occurrences) VALUES (?, ?, ?)')
	
	conn.executemany(query, args)
	
	while True:
		try:
			conn.commit()
		except sqlite3.OperationalError:
			sleep(3)
			continue
		else:
			break

def fetchPatterns():
	global conn
		
	initDBConnection()
	
	conn.row_factory = patternDictFactory
		
	fetchPatternsQuery = ('SELECT * FROM Patterns WHERE predicate NOT LIKE ?')

	c = conn.execute(fetchPatternsQuery, ('http://dbpedia.org/property%',))
	
	conn.row_factory = None
	
	return c.fetchall()

def fetchPatternSources(patternHash):
	global conn
		
	initDBConnection()
		
	c = conn.execute('SELECT subjectWording, objectWording FROM PatternSources WHERE pattern=?', (patternHash,))
	
	return c.fetchall()