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
from configuration import *
from classes import CommonWordingNotFound

def isNumeric(wording):
	return wording[0].isdigit()

def getCommonWording(data, propertyWorder):
 	"""Takes a uri or literal and gets a string presenting it in the most probable way it would be found in the text"""

	commonWording = None

	# Is it a uri or a literal?
 	valueType = data['o']['type']

	value = data['o']['value']

	# The data might be a uri referring to an entity on DBPedia, in that case get the label for the entity 
	if valueType == 'uri' and 'label' in data:
		# Let's get the rfds:label string and return that
		commonWording = data['label']['value']

	elif valueType == 'literal':
		commonWording = data['o']['value']
		
	elif valueType == 'typed-literal':
		# Is this data a magnitude of something, possibly with a unit of measure ?

		datatype = data['o']['datatype'] 
		
		if datatype == namespaces['xsd'] + 'date':
			try:
				commonWording = propertyWorder.getWordedDate(value)
			except ValueError:
				"""Account for impossibile values (e.g. Sep 31st)"""
				pass
				
		elif datatype == namespaces['xsd'] + 'int' or datatype == namespaces['xsd'] + 'integer':
			try:
				commonWording = propertyWorder.getWordedInt(int(value))
			except ValueError:
				"""Sometimes a non deterministic error (i.e. it does not reappear at every execution) returns a NaN for the value"""
				pass
				
		elif datatype == namespaces['xsd'] + 'float' or datatype == namespaces['xsd'] + 'double':
			try:
				commonWording = propertyWorder.getWordedFloat(float(value))
			except ValueError:
				"""Sometimes a non deterministic error (i.e. it does not reappear at every execution) returns a NaN for the value"""
				pass
		
		elif datatype == namespaces['dbpdatatype'] + 'squareKilometre':
			try:
				commonWording = propertyWorder.getWordedSquareKilometre(float(value))
			except ValueError:
				"""Sometimes a non deterministic error (i.e. it does not reappear at every execution) returns a NaN for the value"""
				pass
	
		elif datatype == namespaces['dbpdatatype'] + 'inch':
			try:
				commonWording = propertyWorder.getWordedInch(float(value))
			except ValueError:
				"""Sometimes a non deterministic error (i.e. it does not reappear at every execution) returns a NaN for the value"""
				pass
	
	if commonWording:
		return commonWording
	else:
		raise CommonWordingNotFound
