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
from regex import adjacentWordRegex
from pprint import pprint

class interface():
	def _functionId(obj, nFramesUp):
	    """ Create a string naming the function n frames up on the stack. """
	    fr = sys._getframe(nFramesUp+1)
	    co = fr.f_code
	    return "%s.%s" % (obj.__class__, co.co_name)

	def abstractMethod(obj=None):
	    """ Use this instead of 'pass' for the body of abstract methods. """
	    raise Exception("Unimplemented abstract method: %s" % _functionId(obj, 1))

class LocalisedWikiModule(interface):
	
	@classmethod
	def getLanguage(cls):
		abstractMethod(cls) 

	@classmethod	
	def getWordedFloat(self):
		abstractMethod(cls)
	
	@classmethod
	def getDecimalSeparator(cls):
		abstractMethod(cls)
	
	@classmethod	
	def getThousandsSeparator(cls):
		abstractMethod(cls)
	
	@classmethod
	def getWordedDateFormat(cls, centuryFirstTwoDigits):
		abstractMethod(self)
	
	@classmethod
	def getWordedDate(cls, isoFormattedDate):
		abstractMethod(cls)
	
	@classmethod
	def getWordedInt(cls, value):
		abstractMethod(cls)
	
	@classmethod
	def getWordedFloat(cls, value):
		abstractMethod(cls)

	@classmethod
	def getWordedInch(cls, value, includeUnit=True):
		abstractMethod(cls)

	@classmethod
	def getWordedKilometre(cls, value, includeUnit=True):
		abstractMethod(cls)
		
	@classmethod
	def getWordedSquareKilometre(cls, value, includeUnit=True):
		abstractMethod(cls)
	
	@classmethod	
	def expandTemplateConvert(cls, components):
		abstractMethod(cls)
	
	@classmethod	
	def getCapitalizedWordedClassLabel(cls, typeLabel):
		abstractMethod(cls)

	@classmethod	
	def getUncapitalizedWordedClassLabel(cls, typeLabel):
		abstractMethod(cls)

	@classmethod	
	def adjustText(cls, text):
		abstractMethod(cls)

	@classmethod	
	def partOfProperNoun(cls, word):
		abstractMethod(cls)

class PredicateStatistics():
	def __init__(self,predicateIri):
		self.predicateIri = predicateIri
		self.wordings = set()
		self.precedingStrings = list()
		self.followingStrings = list()
		self.couplings = set()
		
		# These two are dismissed as of April 23, 2013 as their information is not deemed usable
		self.precedingWords = dict()
		self.followingWords = dict()
	
	def toDict(self):
		return {'wordings': self.wordings, 'precedingStrings': self.precedingStrings, 'followingStrings': self.followingStrings }
	
	def addWording(self, wording):
		self.wordings.add(wording)

	def addCoupling(self, iPrec, iFoll):
		self.couplings.add((iPrec,iFoll))
		
	def updateStringCount(self, stringSuperset, string):
		keys = map(lambda (x,y): x, stringSuperset)
		
		try:
			index = keys.index(string)
			value = stringSuperset[index][1]
			stringSuperset.insert(index, (string, value+1))
			stringSuperset.pop(index+1)
			
		except ValueError, e:	
			stringSuperset.append((string,1))
			index = len(stringSuperset)-1
			
		return index
			
	def updatePrecedingStringCount(self, string):
		self.updateStringCount(self.precedingStrings, string)
	
	def updateFollowingStringCount(self, string):
		self.updateStringCount(self.followingStrings, string)
		
	def updatePrecedingWordCount(self, word):
		self.updateStringCount(self.precedingWords, word)
				
	def updateFollowingWordCount(self, word):
		self.updateStringCount(self.followingWords, word)

	def updateWithNewWording(self, commonWording, text):
		self.addWording(commonWording)
		
		p = adjacentWordRegex(commonWording, 3)

		matches = p.findall(text)
		
		for adjacentStrings in matches:
			# Collect matches and remove leading/trailing whitespace
			precString = adjacentStrings[0].strip()
			follString = adjacentStrings[1].strip()
	
			iPrec = self.updatePrecedingStringCount(precString)
			iFoll = self.updateFollowingStringCount(follString)		
			
			self.addCoupling(iPrec, iFoll)
			

class CommonWordingNotFound(Exception):
    pass
	
class RevisionStatementNotFound(Exception):
    pass

class SourceWikiUndeterminable(Exception):
    pass

class RootWordUnidentifiable(Exception):
    pass

class NestedWordingMatch(Exception):
    pass

class UnidentifiableResource(Exception):
	pass

class InvalidSentence(Exception):
	pass

class ShortestPathError(Exception):
	pass
	
class AnnotationError(Exception):
	pass

