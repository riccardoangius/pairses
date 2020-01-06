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

from classes import *
from common import *
from configuration import *
from database import *
from dbpedia import *
from graphs import * 
from model import *
from naivepatterns import *
from patterns import *
from pickling import *
from shared import *
from stanfordcorenlp import *
from timeout import *
from wikipedia import *
from wording import *
import wikidump.model as wikiModel

def getRevisionWikiUrl(sourceWiki, revisionNo):
	"""Only for use with legacy (non-Live) DBPedia"""
	return 'http://' + sourceWiki + '.wikipedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&revids=' + revisionNo
	
