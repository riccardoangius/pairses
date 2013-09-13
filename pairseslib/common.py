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
import sys, os
import re
from configuration import cfg
from stanfordcorenlp import *
def print_n_flush(text):
	print text,
	sys.stdout.flush()
	
def clear_screen():
	os.system('printf "\ec"')

def iszero(x):
	return x == 0

def neg(x):
	return x < 0

def pos(x):
	return x > 0	

def empty(s):
	return len(s) == 0
	
def filenameCompatibleString(string):
	maxLength = int(cfg['predicatenamemaxlength'])
	compatible = re.sub(r'\W+', '.', string[:maxLength])
	return compatible


# Establish RPC connection to the Stanford Core NLP Tools Server
nlp = StanfordCoreNLP()