import random
import math
from .classes import *

def char_range(c1, c2):
	for c in range(ord(c1), ord(c2)+1):
		yield chr(c)

def orderGen( instruments, n, pctMarket, useCaps=True, nEntities=None, minMax=(0.01,100.0) ):
	"""Generates a list of simulated market transactions
	Uses random.{}, so setting seed is possible

	useCaps will set enormous market makers to regulate null and infinite prices

	"""
	if nEntities is None:
		# entities = ['a','b','c','d','e','f']
		nEntities = int(n**0.5)
	
	entities = [ c for i, c in enumerate(char_range('a', 'z')) if i < nEntities ]

	highVal = math.floor(2.71 ** 15)
	lowVal = 1


	nMarket = int(n * pctMarket)
	nLimit  = n - nMarket
	# print(nMarket, nLimit)

	qtyB, qtyS = 0, 0
	ms = []
	for i in range(nMarket):
		# Log-normal quantity
		qty = math.floor(2.71 ** random.randint(1,15))
		side = Side.Buy if i%2 == 0 else Side.Sell
		if side == Side.Buy:
			qtyB += qty
		else:
			qtyS += qty

		# Add this order
		ms.append(
			Order(
				random.choice( instruments ),
				Market(),
				side,
				qty,
				entity = random.choice(entities),
			)
		)
	
	ls = []
	for i in range(nLimit):
		# Log-normal quantity
		qty = math.floor(2.71 ** random.randint(1,15))
		px = random.gauss(0,1)
		side = Side.Buy if px < 0 else Side.Sell
		if side == Side.Buy:
			qtyB += qty
		else:
			qtyS += qty

		# Add this order
		ls.append(
			Order(
				random.choice( instruments ),
				Limit(px),
				side,
				qty,
				entity = random.choice(entities),
			)
		)

	# Shuffle up the orders
	orders = ms + ls
	random.shuffle(orders)
	caps = []
	
	if useCaps:
		highQty = max(qtyB, qtyS)
		for sym in instruments:
			for side, price in ((Side.Buy, minMax[0]), (Side.Sell, minMax[1])):
				caps.append(
					Order(
						sym,
						Limit(price),
						side,
						highQty,
						'market maker',
					)
				)
	# orders = caps + orders
		
	if useCaps:
		return caps, orders
	else:
		return orders



