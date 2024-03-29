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
import os, pickle
from configuration import * 

def pickleDump(data, filename):
	handle = open(filename, 'w') 
 	pickle.dump(data, handle) 
	handle.close()

def pickleLoad(filename):
	handle = open(filename, 'r') 
 	data = pickle.load(handle) 
	handle.close()
	return data