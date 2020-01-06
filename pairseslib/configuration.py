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


# Get the configuration
import ConfigParser
from os.path import expanduser

config = ConfigParser.SafeConfigParser()
config.read('pairses.cfg')

ignored = {	'http://www.w3.org/2000/01/rdf-schema#comment', 
			'http://www.w3.org/2000/01/rdf-schema#label', 
			'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
			'http://www.w3.org/2002/07/owl#sameAs',
			'http://dbpedia.org/ontology/abstract', 
			'http://dbpedia.org/ontology/thumbnail', 
			'http://dbpedia.org/ontology/wikiPageExternalLink',
			'http://xmlns.com/foaf/0.1/name', 
			'http://xmlns.com/foaf/0.1/depiction',
			'http://purl.org/dc/elements/1.1/subject',
			'http://purl.org/dc/terms/subject',
			'http://xmlns.com/foaf/0.1/isPrimaryTopicOf',
			'http://xmlns.com/foaf/0.1/homepage'
			
			}

namespaces = dict()
prefixes = dict()

namespacePrefixes = ''

for key, value in config.items('Namespaces'):
	namespacePrefixes =  namespacePrefixes + '\nPREFIX ' + key + ': <' + value + '>'
	namespaces[key] = value
	prefixes[value] = key

cfg = dict()

for key, value in config.items('Main'):
	cfg[key] = value

endpoint = cfg['sparqlendpointurl']

cfg['home'] = expanduser("~")