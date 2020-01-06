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
import pairseslib
from pprint import pprint
def printRandomArticleTitles(n):
	query = 'SELECT DISTINCT ?s WHERE {\n'
	query += '?s ?p ?o . FILTER ( 1>  <SHORT_OR_LONG::bif:rnd>  (10, ?s, ?p, ?o)) }  LIMIT ' + str(n)
	results = pairseslib.sparqlQuery(query)
	
	for result in results['results']['bindings']:
		print(result['s']['value'].replace('http://dbpedia.org/resource/',''))
	
printRandomArticleTitles(5000)