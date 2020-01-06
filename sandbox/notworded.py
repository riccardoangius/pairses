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
import pairseslib as pl
from pprint import pprint

notWorded = pl.pickleLoad('notWorded.obj')

print 	'<style type="text/css">\
		body { font-family: "Lucida Grande", Arial, sans-serif; } \
		.predicate { background-color: #6699FF; font-weight: bold;}\
		.triple { background-color: #99CCFF;}\
		.link { font-weight: bold;  }\
		</style>'

i = 0
for predicate, triples in sorted(notWorded.iteritems()):
	print '<a href="#predicate%d" class="link">%s</a><br>' % (i, predicate) 
	i+=1
i = 0
print '<table>'
for predicate, triples in sorted(notWorded.iteritems()):
	if 'http://dbpedia.org/property' not in predicate:
		print '<tr class="predicate" id="predicate%d">' % (i)
		print '<td colspan="2">' + predicate + '</td>'
		print '</tr>'
		for triple in triples:
			print '<tr class="triple">'
			print '<td></td>'
			print '<td>'
			pprint(triple['o'])
			print '</td>'
			print '</tr>'
		i+=1
print '</table>'