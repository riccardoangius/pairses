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
import jsonrpclib
from json import loads, dumps
import os, hashlib
from pickling import pickleDump, pickleLoad
from configuration import * 
from classes import *
import unicodedata
cachePath = cfg['snlpcachepath']

class StanfordCoreNLP():
	server = jsonrpclib.Server("http://localhost:8080")

	def parse(self, text, useCache=True):
	
		# Fixes some idiosyncrasies due to wiki markup conversion and text input in Wikipedia
		text = unicode(unicodedata.normalize('NFKD', text))
		
		if text.lower() == 'q' or text.lower() == 'eof':
			"These strings will terminate the SCNLP tools, which we don't want"
			raise InvalidSentence()
		
		if len(text) >= 1000 or text.count(',') > 30:
			"""	A bug in pexpect produces \x07 chars and messes up
				when input is >= 1024 chars (apparently on OS X only)
				Just to be on safe side, we'll ignore sentences with more
			 	than 999 chars, as they are mostly long lists anyway.
			"""
			raise InvalidSentence()
		
		textHash = hashlib.sha224(text.encode("ascii","replace")).hexdigest()
		
		filename = textHash + '.snlpcache'
		path = os.path.join(cachePath, filename)

		if useCache and os.path.exists(path):
			results = pickleLoad(path)
		else:
			parsed = self.server.parse(text)
			results = loads(parsed)

			pickleDump(results, path)
			
		return results