import weakref
import time as t
from .classes import *
from .account import AccountManager
from .piston import Piston



class Engine:
	def __init__(self):
		self.pistons = {}
		self.orderTable = {}
		self.accounts = AccountManager()

	
	def piston(self, symbol:str):
		"""Returns the piston that corresponds with a given symbol.
		"""
		symbol = symbol.upper()
		p = self.pistons.get( symbol, None )
		if p is None:
			# Give this piston a reference of our accounts,
			# so it can also perform transactions per-account
			p = Piston(symbol, accounts=self.accounts.ref)
			self.pistons[symbol] = p
		return weakref.ref(p)


	def cancel(self, orderid):
		"""Cancel an order.
		"""
		sym = self.orderTable.get(orderid,None)
		if sym is not None:
			return self.piston(sym)().exhaust(orderid)
	

	def quote(self, sym):
		p = self.pistons.get(sym, None)
		if p is None:
			return None
		return p.quote


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
	
