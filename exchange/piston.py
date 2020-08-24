import sqlite3
import weakref
from .classes import *


class Piston:
	def __init__(self, sym:str):
		self.sym = sym.upper()

		# Convention:
		# 
		self.orders = {
			'buy': [],
			'sell': []
		}

	def exhaust(self, orderid):
		"""Cancel an outstanding order.
		"""

	def inject(self, order):
		"""Execute this order against our other internal orders.
		"""
		return "Executed order {}".format(str(order))
		


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

		
