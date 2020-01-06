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

import os
import pydot
import networkx as nx
import Image
from configuration import *
from pprint import pprint
import traceback

def fixNodeName(name):
	"""Escape percent signs"""
	if name[0] == '%':
		name = '%' + name
	"""Get rid of prime apostrophes"""	
	name = name.rstrip("'")
	"""Remove extra spaces after pinyin-converted chinese chars"""
	name = name.replace(' -','-')
	return name

def labelPath(graph, p):
	
	pp = zip(p,p[1:])					
	
	extendedPath = [(data['label'].decode(encoding='utf-8'), head.decode(encoding='utf-8')) for tail, head, data in graph.edges(p, data=True) if (tail, head) in pp]
	#labeledPath = map(lambda (x,y,z): (z,y), extendedPath)
	labeledPath = extendedPath
	return labeledPath

def pydotStringToDiGraph(pydotString):

	pydotString = pydotString.encode(encoding='UTF-8')

	P = pydot.graph_from_dot_data(pydotString)

	D = nx.DiGraph(nx.from_pydot(P))
	
	return D

def saveGraph(S, name):
	
	filename = name + '.png'
	path = os.path.join(cfg['outputdir'],filename)
	
	thumbSize = (200,200)
	thumbFilename = name + '_thumb' + '.png'
	thumbPath = os.path.join(cfg['outputdir'],thumbFilename)
	
	# Drawing of the subgraph
	
	T = nx.to_agraph(S)
	
	T.node_attr['labelfontsize']='18.0'
	T.node_attr['style']='filled'
	T.node_attr['color']='#000000'
	T.node_attr['fillcolor']='#ffffff'
	
	T.edge_attr['color']='#6A6A8D'
	T.edge_attr['fontsize']='10.0'
	T.edge_attr['fontcolor']='#6A6A8D'
	T.edge_attr['len']='5.0'

	oid = cfg['objecttag']
	sid = cfg['subjecttag']

	if T.has_node(oid):
		T.get_node(oid).attr['fillcolor'] = '#B4CDCD'
		T.get_node(oid).attr['shape'] = 'egg'
				
	if T.has_node(sid):
		T.get_node(sid).attr['fillcolor'] = '#B4CDCD'
		T.get_node(sid).attr['shape'] = 'egg'
		
  	T.layout(prog='dot')
  	T.draw(path)

	im = Image.open(path)
	im.thumbnail(thumbSize)
	im.save("%s" % thumbPath)