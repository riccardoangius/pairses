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

from timeout import timeout
from SPARQLWrapper import SPARQLWrapper, JSON
from classes import *
from configuration import *
from json import loads 
from pickling import pickleDump, pickleLoad
import os, hashlib
from pprint import pprint

cachePath = cfg['dbpcachepath']

def escapeString(s):
	return unicode.replace(s, '"','\\"')

@timeout(60)
def sparqlQuery(query, useCache=True, endpoint=cfg['sparqlendpointurl']):
	"""Retrieves the results of SPARQL query to the specified endpoint"""
	"""Cached results are returned when available"""

	queryHash = hashlib.sha224(query.encode("ascii","replace")).hexdigest()

	filename = queryHash + '.dbpcache'
	path = os.path.join(cachePath, filename)

	if useCache and os.path.exists(path):
		result = pickleLoad(path)
	else:
		sparql = SPARQLWrapper(endpoint)
		query = namespacePrefixes + query
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		queryResult = sparql.query()
		
		jsonEncodedResult = queryResult.response.read()

		# We have to fix some invalid \U escapes from DBPedia with proper \u ones
		jsonEncodedResult = jsonEncodedResult.replace('\U','\u')
	
		result = loads(jsonEncodedResult)
		
		if useCache:
			pickleDump(result, path)

	return result
	
def fetchSubjectTriples(subjectIRI, lang, excludeRawTriples = True, useCache=True):
	"""Performs a SPARQL query returning all the RDF statements with subjectUri as subject"""
	
	if 'http' in subjectIRI:
		subjectIRI = '<%s>' % subjectIRI
	
	#TODO: Make prettier
	query = 'SELECT DISTINCT ?p ?o ?label WHERE {\n'
	query += '{ ' + subjectIRI + ' ?p ?o .\n'
	query += 'FILTER('
	
	if excludeRawTriples:
		query += '!STRSTARTS(STR(?p), "http://dbpedia.org/property") &&'
	
	query += '(langMatches(lang(?o),\'' + lang + '\') || isUri(?o) || (isLiteral(?o) && datatype(?o) != \'xsd:string\') )'
	query += ') '
	
	query += '}\n'
	query += 'OPTIONAL {\n'
	query += '{ ?o rdfs:label ?label }\n'
	query += 'UNION\n'
	query += '{ ?redirect dbpedia-owl:wikiPageRedirects ?o . ?redirect rdfs:label ?label } . FILTER (langMatches(lang(?label),\'' + lang + '\'))\n'
	query += '}\n'

	query += '}\n'
	results = sparqlQuery(query, useCache)
	
	return results['results']['bindings']

def otherLabels(subjectIRI, lang):
	"""Returns all the labels for resources redirecting to subjectUri"""
	
	if 'http' in subjectIRI:
		subjectIRI = '<%s>' % subjectIRI
	
	#TODO: Make prettier
	query = 'SELECT DISTINCT ?label WHERE {'
	query += ' ?redirect dbpedia-owl:wikiPageRedirects ' + subjectIRI + ' .'
	query += ' ?redirect rdfs:label ?label '
	query += ' FILTER(langMatches(lang(?label),\'' + lang + '\'))'
	query += '}'
	results = sparqlQuery(query)

	labels = set({data['label']['value'] for data in results['results']['bindings']})

	return labels
	
def labelToResource(label, lang):
	"""Returns the first DBPedia resource with label as its rdfs:label or the DBPedia resource to which the label's subject is a redirect"""
	#TODO: Make prettier
	label = escapeString(label)
	
	query = 'SELECT DISTINCT ?normalized WHERE {'
	query += '{ ?normalized rdfs:label "' + label + '"@' + lang + ' } '
	query += ' UNION '
	query += '{ ?p rdfs:label "' + label + '"@' + lang + ' . '
	query += '?p dbpedia-owl:wikiPageRedirects ?normalized }'
	query += 'FILTER (STRSTARTS(STR(?normalized), "http://dbpedia.org/resource") && !CONTAINS(STR(?normalized),"Category%3A"))'
	query += '}'
	
	results = sparqlQuery(query)
	
	try:
		return results['results']['bindings'][0]['normalized']['value']
	except:
		raise UnidentifiableResource

def getClasses(subjectLabel, lang):
	"""Returns all the types associated with entities having subjectLabel as their label"""
	
	subjectLabel = escapeString(subjectLabel)
	lowerCaseSL = subjectLabel.lower()

	# Ok so this query is not the most elegant
	# but it is certainly more performing than 
	# what suggested by OpenLinkSW (i.e. use FILTER) for case-insensitive matching of literals
	query = 'SELECT DISTINCT ?t WHERE {' \
				'?s rdfs:range ?t.' \
				'{' \
				'{ { ?s rdfs:label "%s"@%s } UNION { ?s rdfs:label "%s"@%s } } ' \
				'UNION' \
				'{ { { ?r rdfs:label "%s"@%s } UNION { ?r rdfs:label "%s"@%s } } . ?r dbpedia-owl:wikiPageRedirects ?s } ' \
				'}.'\
				'FILTER(STRSTARTS(STR(?s), "http://dbpedia.org/")) ' \
				'}' %(subjectLabel, lang, lowerCaseSL, lang, subjectLabel, lang, lowerCaseSL, lang)

	results = sparqlQuery(query)

	classes = map(lambda x: x['t']['value'], results['results']['bindings'])

	if len(classes) < 1:

			query = 'SELECT DISTINCT ?t WHERE {' \
						'?s rdf:type ?t.' \
						'{' \
						'{ { ?s rdfs:label "%s"@%s } UNION { ?s rdfs:label "%s"@%s } } ' \
						'UNION' \
						'{ { { ?r rdfs:label "%s"@%s } UNION { ?r rdfs:label "%s"@%s } } . ?r dbpedia-owl:wikiPageRedirects ?s } ' \
						'}.'\
						'FILTER(STRSTARTS(STR(?s), "http://dbpedia.org/")) ' \
						'}' %(subjectLabel, lang, lowerCaseSL, lang, subjectLabel, lang, lowerCaseSL, lang)
						
 			results = sparqlQuery(query)

			classes = map(lambda x: x['t']['value'], results['results']['bindings'])
			
			if len(classes) < 1:
				classes = [expandIRI('owl:Thing')]

	return classes

def getSubjObjRelation(subjectLabel, objectLabel, lang):
	"""Returns all the predicates in triples pertaining subjectLabel and objectLabel"""
	
	subjectLabel = escapeString(subjectLabel)
	objectLabel = escapeString(objectLabel)
	
	query = 'SELECT DISTINCT ?p WHERE {'\
			'?s ?p ?o.' \
			'{ { ?s rdfs:label "%s"@%s } UNION' \
			'{?r rdfs:label "%s"@%s . ?r dbpedia-owl:wikiPageRedirects ?s }' \
			'FILTER(STRSTARTS(STR(?s), "http://dbpedia.org/resource/")) }.' \
			'{ { ?o rdfs:label "%s"@%s } UNION' \
			'{?r rdfs:label "%s"@%s . ?r dbpedia-owl:wikiPageRedirects ?o }' \
			'FILTER(STRSTARTS(STR(?o), "http://dbpedia.org/resource/")) }' \
			'}' % (subjectLabel, lang, subjectLabel, lang, objectLabel,lang, objectLabel,lang)

	results = sparqlQuery(query)
	
	if len(results['results']['bindings']) < 1:
		return list()
	
	relations = map(lambda x: x['p']['value'], results['results']['bindings'])

	return relations

def getRevisionNo(dbpediaData):
	for po in dbpediaData:
		if po['p']['value'] == 'http://www.w3.org/ns/prov#wasDerivedFrom':
			return re.findall('.*=(\d+)',po['o']['value'])[0]
	raise RevisionStatementNotFound('Could not identify source article revision.')

def getSourceWiki(dbpediaData):
	for po in dbpediaData:
		if po['p']['value'] == 'http://www.w3.org/ns/prov#wasDerivedFrom':
			return re.findall('.*//(\w+)\.wikipedia\.org.*',po['o']['value'])[0]
	raise SourceWikiUndeterminable('Could not identify source article wiki.')
	
def getValuesForPredicate(triples, predicateIRI):
		predicateIRI = expandIRI(predicateIRI)
			
		values = set()
		
		for triple in triples:
			if triple['p']['value'] == predicateIRI:
				values.add(triple['o']['value'])
				
		return values

def getLabelsForPredicate(triples, predicateIRI):
		predicateIRI = expandIRI(predicateIRI)
	
		values = set()
		for triple in triples:
			if triple['p']['value'] == predicateIRI:
				if 'label' in triple:
					values.add(triple['label']['value'])
					
		return values
		
def expandIRI(IRI):
	if 'http' not in IRI:
		prefix, name = IRI.split(':')
		expanded = namespaces[prefix] + name
	else:
		expanded = IRI
		
	return expanded
	
	
	
	
	