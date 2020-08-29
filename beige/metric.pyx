import operator
from sortedcontainers import SortedDict
from .classes import *


class MarketQuote:
	"""Efficiently keeps track of the running market quote.
	"""
	def __init__(self):
		self.info = {
			Side.Buy  : SortedDict(),
			Side.Sell : SortedDict(),
		}
	
	def removeLimit ( self, side, px, qty ):
		'''Remove a limit order from the book
		'''
		px = abs(px)
		newQty = self.info[side][px] - qty

		# Should we remove this entry?
		if newQty == 0:
			self.info[side].pop(px)

		# Well, then just remove the limit order
		else:
			self.info[side][px] = newQty



	def addLimit ( self, side, px, qty ):
		'''Adds a limit order to the book
		'''
		px = abs(px)
		j = self.info[side].get(px,0) + qty
		self.info[side][px] = j


	@property
	def quote(self):
		try:
			bid = self.info[Side.Buy].keys()[-1]
			bids = self.info[Side.Buy][bid]
		except:
			bid, bids = None, 0

		try:
			ask = self.info[Side.Sell].keys()[0]
			asks = self.info[Side.Sell][ask]
		except:
			ask, asks = None, 0

		return bid, ask, bids, asks
