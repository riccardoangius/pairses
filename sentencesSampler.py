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
from pairseslib import pickleLoad
import random
import re, codecs
sentencesPopulation = pickleLoad('sentencesPopulation.obj')

print('*')
k = 200

random.seed()
randomSample = random.sample(filter(lambda x: x != '', sentencesPopulation), k)

with codecs.open('sentencesSample.txt', 'a') as outputFile:
	for sentence in randomSample:
		outputFile.write(sentence.encode(encoding='utf-8') + '\n')

	