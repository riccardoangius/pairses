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

import os, re, pickle, shutil
from configuration import * 
from wording import *
from classes import *

def adjacentWordRegex(commonWording, maxAdjacentWords):
	wordRange = '(?:\'|\s)[A-z0-9_\-()"%]+[;,:]?'
	
	# Case insensitive regex
	regex = '(?i)'			
	regex += '(?:(?:^|\.)[^.]*?' + '((?:' + wordRange + '){0,' + str(maxAdjacentWords) + '})\s' + re.escape(commonWording) + '[;,:]?' + '((?:' + wordRange + '){0,' + str(maxAdjacentWords) + '})' + '(?:\s[^.]*?)?\.(?:[^\d]|$))'
	
	return re.compile(regex)

def wordingIsInText(commonWording, text):
	p = adjacentWordRegex(commonWording, 1)
	if p.search(text):
		return True
	else:
		return False

def naiveStatistics(title, text, dbpediaData, propertyWorder, naivePredicateStatistics, naiveSubjectStatistics, adjacent=3, verbose=True):
	presProps = set()
	props = set()
	
	for prop in dbpediaData:
		if prop['p']['value'] in ignored:
			continue
		
		try:
			commonWording = getCommonWording(prop,propertyWorder)
		except CommonWordingNotFound:
			continue

		assert(commonWording != '')
		if wordingIsInText(commonWording,text):
			presProps.add(prop['p']['value'])			
		
			if not prop['p']['value'] in naivePredicateStatistics:
				naivePredicateStatistics[prop['p']['value']] = PredicateStatistics(prop['p']['value'])
	
			naivePredicateStatistics[prop['p']['value']].updateWithNewWording(commonWording, text)
					
		props.add(prop['p']['value'])

	# Present
	p = len(presProps)
	
	# Total properties
	i = len(props)
	
	# Not present
	np = i-p
	
	if not naiveSubjectStatistics:
		header = 'Title, Total Properties, Present, Not present, P/NP Ratio\n'
		
		naiveSubjectStatistics.append(header)
	
	statistics = '"' + title + '",' + str(i) + ',' + str(p) + ',' +  str(np)  + ',' + str(float(p)/float(i))
	
	naiveSubjectStatistics.append(statistics)

def htmlTable(element,depth=0):

	html = ''

	html += '<table>'
	
	html += '<tr class="predicate">'
	html += '<td class="predicateName">' + element.predicateIri + '</td>'
	html += '<td>'
	html += '<table><tr class="commonWordings"><td>Commong Wordings</td><td>' + '; '.join(element.wordings) + '</td></tr>'	
	
	html += '<tr class="precedingStrings"><td>Preceding Strings</td><td>'
	
	html += '<table>'

	i = 0
	for pair in sorted(element.precedingStrings, key = lambda pair: pair[1], reverse = True):
		html += '<tr><td>'
		if pair[0] == '':
			html += '[[the empty string]]'
		else:
			html += pair[0]
		html += '</td><td class="count">'  +  str(pair[1])

		html += '</td></tr>'
		i+=1
		if i > 4:
			break
	html += '</table>'
	
	html += '<tr class="followingStrings"><td>Following Strings</td><td>'
	
	html += '<table>'
	
	i = 0
	for pair in sorted(element.followingStrings, key = lambda pair: pair[1], reverse = True):
		html += '<tr><td class="string">'
		if pair[0] == '':
			html += '[[the empty string]]'
		else:
			html += pair[0]
		html += '</td><td class="count">'  +  str(pair[1])
		html += '</td></tr>'
		i+=1
		if i > 4:
			break
			
	html += '</table>'
	
	html += '</td></tr></table>'
	
	html += '</td>'
	html += '</tr>'
	
	html += '</table>'

	return html

def naivePredicateStatisticsToHTML(naivePredicateStatistics):
	
	i = 1
	j = 0
	resourcesDir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources'))
	headerFile = os.path.join(resourcesDir, 'header.html')
	footerFile = os.path.join(resourcesDir, 'footer.html')
	styleFile = os.path.join(resourcesDir, 'style.css')
	indexFile = cfg['naivepredicatestatisticsoutput'] + '_'  + 'index' + '.' + cfg['naivepredicatestatisticsoutputext']
	
	outputDir = os.path.dirname(indexFile)
	targetStyleFile = os.path.join(outputDir, 'style.css')
	shutil.copyfile(styleFile, targetStyleFile)
	
	header = ' '.join(open(headerFile,'r').readlines()[:])
	pageHeader = header + '<h3><a href="' + indexFile + '">Back to index</a></h3>'
	footer = ' '.join(open(footerFile,'r').readlines()[:])

	outputFile = cfg['naivepredicatestatisticsoutput'] + '_' + str(j) + '.' + cfg['naivepredicatestatisticsoutputext']
	output = open(outputFile, 'w')
	output.write(pageHeader)

	for key, element in naivePredicateStatistics.items():

		byPropHtml = htmlTable(element).encode('utf-8')
		output.write(byPropHtml)

		if i%10 == 0:
			j += 1
			output.write(footer)
			output.close()
			outputFile = cfg['naivepredicatestatisticsoutput'] + '_' + str(j) + '.' + cfg['naivepredicatestatisticsoutputext']
			output = open(outputFile, 'w')
			output.write(pageHeader)

		i += 1
		
	output.write(footer)
	output.close()
	
	
	outputFile = indexFile
	output = open(outputFile, 'w')
	output.write(header)
	for i in range(0, j):
		filename = cfg['naivepredicatestatisticsoutput'] + '_'  + str(i) + '.' + cfg['naivepredicatestatisticsoutputext']
		output.write('<a href="' + filename + '">Page ' + str(i) + '</a><br>')
	output.close()