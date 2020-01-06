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

from pairseslib.classes import LocalisedWikiModule
import re, unicodedata

class EnglishWikipediaModule(LocalisedWikiModule):
	
	language = 'en'
	
	def getLanguage(cls):
		return cls.language
	
	def getDecimalSeparator(cls):
		return '.'

	def getThousandsSeparator(cls):
		return ','

	def getWordedDateFormat(cls, centuryFirstTwoDigits):
		"Returns the most common date format in articles written in lang"
		if centuryFirstTwoDigits > 0:
			c = unicode(centuryFirstTwoDigits)
		else:
			c = ''
		return unicode('%B %d, ' + c + '%y')

	def getWordedDate(cls, isoFormattedDate):
		from datetime import datetime, date
		from string import replace

		negativeYear = (isoFormattedDate[0] == '-')

		if negativeYear:
			isoFormattedDate = isoFormattedDate[1:]

		components = isoFormattedDate.split('-')
		year = int(components[0])%100+1900
		centuryFirstTwoDigits = int(components[0])/100
		month = int(components[1])
		day = int(components[2])

		#TODO: Deal with invalid dates (e.g. September 31st)
		
		dateObject = date(year, month, day)
		# Applies date format to isoFormattedDate
		format = cls.getWordedDateFormat(centuryFirstTwoDigits)
		formattedDate = dateObject.strftime(format)
		
		# Here we remove any leading zeroes (better than relying of platform-specific format codes that don't have leading zeroes)
		commonWording = replace(formattedDate, ' 0',' ')

		if negativeYear:
			commonWording = commonWording + ' B.C.'

		return unicode(commonWording)

	def getWordedInt(cls, value):

		negative = value < 0

		value = abs(value)

		if value == 0:
			commonWording = '0'
		else:
			commonWording = ''
			separator = cls.getThousandsSeparator()

			text = str(value)
			i = len(text)
			k = max(0,i-3)
			commonWording = text[k:i]

			while (k > 0):
				i = i-3
				k = max(0,i-3)
				commonWording = text[k:i] + separator + commonWording

			if negative:
				commonWording = '-' + commonWording

		return unicode(commonWording)

	def getWordedFloat(cls, val):
		rounded = int(round(val,0))
		return cls.getWordedInt(rounded)

	def getWordedInch(cls, val, includeUnit=True):
		rounded = int(round(val,0))
		worded = cls.getWordedFloat(rounded)
		if includeUnit:
			worded += ' in'
		return worded

	def getWordedKilometre(cls, val, includeUnit=True):
		rounded = int(round(val,0))
		worded = cls.getWordedFloat(rounded)
		if includeUnit:
			worded += ' km'
		return worded

	def getWordedSquareKilometre(cls, val, includeUnit=True):
		rounded = int(round(val,0))
		worded = cls.getWordedFloat(rounded)
		if includeUnit:
			worded += ' km2'
		return worded

	def expandTemplateConvert(cls, components):
		"""Conversion factors from https://en.wikipedia.org/wiki/Template:Convert/list_of_units"""
		
		# Account for negative values
		factor = 1
		value = unicode(unicodedata.normalize('NFKD', components.pop(0)))
		
		# Remove thousands separator
		value = value.replace(',','')
		
		
		if not value.isnumeric():
			expansion = value
			return expansion
			
		minus = re.compile(ur'(-|\u2212|&minus;)')
		if minus.match(value):
			factor = -1
			value = minus.sub('', value)
		
		value = float(value)*factor
		value2 = None
		
		next = components.pop(0)
		
		if next == 'and' or next == 'to':
			"""Interval"""
			# TODO: Expand intervals properly, for now we only get the lower bound
			value2 = components.pop(0)
			unit = components.pop(0)
		else:
			unit = next
		
		if unit == 'mi':
			"""Convert to km"""
			converted = value * 1.609344
			expansion = cls.getWordedKilometre(converted)
		
		elif unit == 'km':
			expansion = cls.getWordedKilometre(value)
		
		elif unit == 'sqmi':
			"""Convert to square km^2"""
			converted = value * 2.589988110336
			expansion = cls.getWordedSquareKilometre(converted)
		
		elif unit == 'km2':
			expansion = cls.getWordedSquareKilometre(value)
		
		
		else:
			expansion = unicode()
				
		return expansion
	
	def partOfProperNoun(cls, word):
		return word.istitle()

	def getClassLabelWording(cls, classLabel):
		
		capitalized = 'The '
		uncapitalized = 'the '
		
		uncapitalizedClassLabel = classLabel[0].lower() + classLabel[1:]
		
		capitalized += uncapitalizedClassLabel
		uncapitalized += uncapitalizedClassLabel
		
		return capitalized, uncapitalized
	
	def normalizeDate(cls, match):
		day = match.group('day')
		month = match.group('month')
		year = match.group('year')
		# TODO: have this work through getWordedDate()
		worded = month + ' ' + day
		if year:
			worded += ', ' + year
		return worded
		
	def adjustText(cls, text):
		"""Perform various adjustments so to have text correctly be parsed by
		 the SCNLP tools"""
		
		"""Adjust dates so to transform strings such as '21 August' to 'August
		 21' and have them recognized by the SCNLP tools"""
		months = (u'January|February|March|April|May|June|July'
					'August|September|October|November|December')
		dates = re.compile('(?P<day>\d{1,2})\s+(?P<month>%s)(\s+(?P<year>(\d{2,4})))?' % months)
		text = dates.sub(cls.normalizeDate, text)
		# Strip any remaining HTML (WikiExtractor is not perfect)
		htmlTags = re.compile('<[^>]+>')
		
		text = htmlTags.sub("", text)
		
		return text