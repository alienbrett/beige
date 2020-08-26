import weakref
import time as t
from .classes import *
from .lattice import Lattice
from .manager import OrderManager


def sideQuote ( lattice, manager ):
	price, size = None, 0
	for oid in lattice:
		o = manager.get(oid)
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

		# Transaction history
		self.txs = []

		self._manager = OrderManager()

		# Outstanding orders
		self.table = {
			Side.Buy  : Lattice(),
			Side.Sell : Lattice()
		}



	@property
	def quote(self):
		"""Returns (bid,ask, bidsize, asksize)
		"""
		bid, bidsize = sideQuote ( self.table[Side.Buy],  self._manager )
		ask, asksize = sideQuote ( self.table[Side.Sell], self._manager )
		self._quote = (bid, ask, bidsize, asksize)
		return self._quote


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
		price = order['price']['price']
		time  = order['submitted']
		if side == Side.Buy:
			price = 0 - price
		return side, price, time



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
		
		remaining = lambda o: o['qty'] - o['filled']

		order = self._manager.get(orderid)
		other = self._manager.get(otherid)

		tx['px'] = order['price']['price']

		# Find the lower of the two remaining quantities
		tx['qty'] = min( remaining(order), remaining(other))
		tx['time'] = t.time()

		self.txs.append(tx)
		# If the order is still outstanding
		if not self._manager.fill( otherid, tx['px'], tx['qty'] ):
			# We should pop this order
			side, price, time = Piston.extractIds(other)
			self.table[ otherside ].pop(price, time)
		
		return self._manager.fill( orderid, tx['px'], tx['qty'] )


			

	def inject(self, order):
		"""Execute this order against our other internal orders.
		"""
		# Ensure this key doesn't already exist here
		orderid = order.get('id')
		if self._manager.get(orderid) is not None:
			raise ValueError('id {0} already exists in this piston ({1})'.format(orderid, self.sym))

		# Insert into our records
		self._manager.add(orderid, order)

		side, price, time = Piston.extractIds(order)

		cond = True
		while cond:
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

			if newSpread is not None and newSpread <= 0:
				# Execute this against current shares
				cond = self.combust ( orderid, side, price, time)

			else:
				# Then we should insert
				self.table[side].insert ( price, time, orderid )
				break


	def status(self, orderid):
		"""Return copy of the outstanding order
		"""
		return self._manager.get(orderid)







class Engine:
	def __init__(self):
		self.pistons = {}
		self.orderTable = {}
	
	def piston(self, symbol:str):
		"""Returns the piston that corresponds with a given symbol.
		"""
		symbol = symbol.upper()
		p = self.pistons.get( symbol, None )
		if p is None:
			p = Piston(symbol)
			self.pistons[symbol] = p
		return weakref.ref(p)


	def cancel(self, orderid):
		"""Cancel an order.
		"""
		sym = self.orderTable.get(orderid,None)
		if sym is not None:
			return self.piston(sym)().exhaust(orderid)

	def submit(self, order):
		"""Submit an order for execution
		"""
		sym = order['sym']

		# Get an id from this order
		orderid = hash(str(order))
		order['id'] = orderid
		# Add to our lookup table so we can refer to the proper piston
		self.orderTable[order['id']] = sym

		self.piston(sym)().inject(order)
		return orderid

		
	def status(self, orderid):
		"""Retreive the information corresponding to an outstanding order
		"""
		sym = self.orderTable.get(orderid,None)
		if sym is not None:
			return self.piston(sym)().status(orderid)
	
