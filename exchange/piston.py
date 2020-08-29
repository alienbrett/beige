import weakref
import time as t
from .metric import MarketQuote
from .classes import *
from .lattice import Lattice
from .manager import OrderManager


class Piston:
	def __init__(self, sym:str, accounts):
		self.sym = sym.upper()
		self.accounts = accounts()

		# Transaction history
		self.txs = []

		self._manager = OrderManager()

		# Outstanding orders
		self.table = {
			Side.Buy  : Lattice(),
			Side.Sell : Lattice(),
		}
		# Quickly generates new quotes
		self._metrics = MarketQuote()


	def _sideQuote ( self, side, fast=False ):
		if fast:
			prefix = 'bid' if side == Side.Buy else 'ask'
			price =  self._quoteVals.get( prefix, None )
			size = self._quoteVals.get( prefix+'s',0 )
			return price, size
		else:
			price, size = None, 0
			for oid in self.table[side]:
				o = self._manager.get(oid)
				p = o['price']['price']
				if price is None:
					price = p
				elif price != p:
					break

				size += o['qty']
			return price, size
		


	@property
	def quote(self, fast=True):
		"""Returns (bid,ask,last bidsize, asksize, lastsize, lasttime)
		"""
		# print("QUOTE")
		bid, ask, bidsize, asksize = self._metrics.quote
		# print(bid,ask)
		if not fast:
			bid, bidsize = self._sideQuote ( Side.Buy )
			ask, asksize = self._sideQuote ( Side.Sell )
			# print(bid,ask)

		try:
			lastTx = self.txs[-1]
			last, lastsize = lastTx['px'], lastTx['qty']
		except:
			last, lastsize = None, 0
		return bid, ask, last, bidsize, asksize, lastsize


	@property
	def strQuote(self):
		q = self.quote
		q = [ (x if x is not None else 0) for x in q ]
		return '${0:,.4f} ${1:,.4f} ({2:,}x{3:,})'.format(
			q[0],
			q[1],
			q[2],
			q[3]
		)
		pass


	@staticmethod
	def extractIds(order):
		side  = order['side']
		price = order['price'].get('price')
		time  = order['submitted']
		if side == Side.Buy and price is not None:
			price = 0 - price
		return side, price, time

	@property
	def book(self):
		print('Buy: ', [ x for x in self.table[Side.Buy] ])
		print('Sell: ', [x for x in self.table[Side.Sell] ])


	def exhaust(self, orderid):
		"""Cancel an outstanding order.
		"""
		o = self._manager.get(orderid)
		
		result = None
		try:
			side, price, time = self.extractIds( o )
			if side is not None:

				# Remove this from our book
				resultId = self.table[side].pop(price, time)

				# Change our quote book
				if price is not None:
					qty = o['qty']
					self._metrics.removeLimit( side, price, qty )

				# Update the statuses
				self._manager.cancel(orderid)
		except:
			pass
		return result



	def combust(self, orderid, side, price, time):
		"""Take an order, and match it with a single corresponding order.
		May fill or partially fill.
		Will call self.clearOut(...) to remove empty suborders
		"""
		tx = {}
		otherside = (Side.Sell if side == Side.Buy else Side.Buy)
		otherid = next( x for x in self.table[ otherside ] )
		
		# Short way to find remaining shares on the order
		remaining = (lambda o: o['qty'] - o['filled'])

		order = self._manager.get(orderid)
		other = self._manager.get(otherid)

		# Find the lower of the two remaining quantities
		tx['qty'] = min( remaining(order), remaining(other) )
		tx['px'] = price
		tx['time'] = time

		# Update the accounts
		self.accounts.exchange(
			buyer  = order['acct'],
			seller = other['acct'],
			symbol = order['sym'],
			qty    = tx['qty'] * (1 if side == Side.Buy else -1),
			unitPx = price
		)

		# Remove this order from the book
		self._metrics.removeLimit(
			otherside,
			other['price']['price'],
			tx['qty']
		)

		# Make sure we log this 
		self.txs.append(tx)

		# If the order is still outstanding
		if not self._manager.fill( otherid, price, tx['qty'] ):
			# We should pop this order
			tmp = Piston.extractIds(other)
			self.table[ tmp[0] ].pop(tmp[1], tmp[2])
		
		return self._manager.fill( orderid, price, tx['qty'] )


			

	def inject(self, order):
		"""Execute this order against our other internal orders.
		"""
		# Ensure this key doesn't already exist here
		orderid = order.get('id')
		if self._manager.get(orderid) is not None:
			raise ValueError('id {0} already exists in this piston ({1})'.format(orderid, self.sym))

		# Insert into our records
		self._manager.add(orderid, order)

		cond = True
		while cond:
			side, price, time = Piston.extractIds(order)
			# Decide whether this price should be used
			newSpread = 1
			bid, ask, _, _, _, _ = self.quote
			# print(bid,ask)
			marketPx = (ask if side == Side.Buy else bid)
			
			if price is None:
				if marketPx is None:
					# We can't have a market order without limits
					raise RuntimeError("Market order placed without any matching limits.")
				else:
					price = marketPx
					newSpread = 0
			else:
				price = abs(price)
				if marketPx is not None:
					if side == Side.Sell:
						newSpread = price - marketPx
					else:
						newSpread = marketPx - price

			if newSpread <= 0:
				# Execute this against current shares
				cond = self.combust ( orderid, side, price, time)

			else:
				# Then we should insert
				side, price, time = Piston.extractIds(order)

				# update our quote book
				self._metrics.addLimit(
					order['side'],
					price,
					order['qty']
				)

				# Insert this limit into the book
				self.table[side].insert ( price, time, orderid )
				break

	def status(self, orderid):
		"""Return copy of the outstanding order
		"""
		return self._manager.get(orderid)





