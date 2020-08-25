import sqlite3
import weakref
from .classes import *
from .lattice import Lattice


def sideQuote ( lattice ):
	price, size = None, 0
	for o in lattice:
		p = o['price']['price']
		if price is None:
			price = p
		elif price != p:
			break

		size += o['qty']
	return price, size
		


class Piston:
	def __init__(self, sym:str):
		self.sym = sym.upper()

		# Order position lookup
		self.odict = {}
		# Each entry should be like
		# (side.Buy, -14.51, 123457.1)
		#  [0] => buy or sell
		#  [1] => price tier (negative for buy, pos for sell, for lattice ordering)
		#  [2] => timestamp

		self.orders = {
			Side.Buy  : Lattice(),
			Side.Sell : Lattice()
		}
		# Set flags
		self._refreshQuote = True



	@property
	def quote(self):
		"""Returns (bid,ask, bidsize, asksize)
		"""
		# if self._refreshQuote:
		bid, bidsize = sideQuote ( self.orders[Side.Buy] )
		ask, asksize = sideQuote ( self.orders[Side.Sell] )
		self._quote = (bid, ask, bidsize, asksize)
		# self._refreshQuote = False
		return self._quote

	@property
	def strQuote(self):
		q = self.quote
		return '${0:,.4f} ${1:,.4f} ({2:,}x{3:,})'.format(
			q[0],
			q[1],
			q[2],
			q[3]
		)

	@staticmethod
	def extractIds(order):
		side = order['side']
		price = order['price']['price']
		time = order['time']
		if side == Side.Buy:
			price = 0 - price
		return side, price, time



	def exhaust(self, orderid):
		"""Cancel an outstanding order.
		"""
		side, price, time = self.odict.get ( orderid, (None, 0.0, 0.0) )
		result = None
		if side is not None:
			result = self.orders[side].pop(price, time)

		return result
	
	def clearOut ( self, side ):
		"""Removes completed orders
		"""
		pops = []
		for order in self.orders[side]:
			side, price, time = Piston.extractIds(order)
			qty = order['qty']
			if qty == 0:
				pops.append((price, time))

			# Experimental, for speed improvements
			else:
				break
			# print(side, price, time)

		for p in pops:
			x = self.orders[side].pop(p[0], p[1])
		# print("MY BINS!")
		# for x in self.orders[side]:
		# 	print(x)


	def combust(self, order, side, price, time):
		# print("Combusting...")
		buy, sell = None, None

		tx = {}
		if side == Side.Buy:
			buy = order
			sell = next( x for x in self.orders[Side.Sell] )
			tx['px'] = sell['price']['price']
		else:
			buy = next( x for x in self.orders[Side.Buy] )
			sell = order
			tx['px'] = buy['price']['price']

		tx['qty'] = min(buy['qty'], sell['qty'])
		
		if tx['qty'] > 0:

			buy['qty'] -= tx['qty']
			sell['qty'] -= tx['qty']
			print("TRANSACTION:", tx)
		# else:
			# print("One or both orders are zero")

		# Remove the top entry, only if its empty
		self.clearOut(
			side.Sell if side == Side.Buy else Side.Buy
		)
		# print("order qty (combust):", buy['qty'], sell['qty'])
		# return (tx['qty'] != 0)
			
		

	def inject(self, order):
		"""Execute this order against our other internal orders.
		"""

		side, price, time = Piston.extractIds(order)
		# print(side, price, time)

		while True:
			# print("order qty (inject):", order['qty'])
			# self._refreshQuote = True
			# Decide whether this price should be used
			newSpread = 1
			if side == Side.Buy:
				p = self.quote[1]
				if p is not None:
					newSpread = p + price
			else:
				p = self.quote[0]
				if p is not None:
					newSpread = price - p
			
			# print('my best alternative:', p, 'spread', newSpread)
			# print('spread:', newSpread)

			if newSpread is not None and newSpread <= 0:
				# Execute this against current shares
				self.combust ( order, side, price, time)

			else:
				# Then we should insert
				self.orders[side].insert ( price, time, order )
				# print("Breaking loop")
				break

		# print()
		# self._refreshQuote = True
		







class Engine:
	def __init__(self):
		self.pistons = {}
	
	def piston(self, symbol:str):
		"""Returns the piston that corresponds with a given symbol.
		"""
		symbol = symbol.upper()
		p = self.pistons.get( symbol, None )
		if p is None:
			p = Piston(symbol)
			self.pistons[symbol] = p
		return weakref.ref(p)


	def submit(self, order):
		sym = order['sym']

		self.piston(sym)().inject(order)
		
