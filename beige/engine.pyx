import weakref
import uuid
import pandas as pd
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
		return self.piston(sym.upper()).quote
	

	@property
	def quotes(self):
		df = pd.DataFrame(
			data = [ piston.quote for piston in self.pistons.values() ],
			columns = ['bid','ask','last','bidsize','asksize','lastsize'],
			index = list(self.pistons.keys())
		)
		return df
		
	@property
	def txs(self):
		df = pd.DataFrame(
			[
				{ **x, 'sym': sym}
				for sym, p in self.pistons.items()
				for x in p.txs
			]
		)
		return df

	def submit(self, order):
		"""Submit an order for execution
		"""
		sym = order['sym']

		# Get an id from this order
		# orderid = uuid.UUID( str(order) )
		orderid = uuid.uuid4( )
		# print(orderid)
		# print(type(orderid))
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
	
