import unittest
import time
import random
from decimal import *
from exchange import *

class TestOrders ( unittest.TestCase ):
	def test_order_pricing (self):
		
		# Are market orders correct?
		market = Market()
		self.assertEqual(market, {'type':'market'})

		# Are limit orders correct for arbitrary limits?
		for test, correct in [
			(10.0, Decimal(10)),
			(0.0001, Decimal('0.0001')),
			(1/3.0, Decimal('0.3333'))
		]:
			l = Limit(test)

			self.assertEqual ( l, {'type':'limit','price':correct} )

		
	def test_orders ( self ):
		# print("Testing orders")
		self.assertEqual (
			Order(
				'spy',
				Market(),
				Side.Buy,
				100,
			),
			{
				'price': {'type':'market'},
				'sym': 'SPY',
				'qty': 100,
				'side': Side.Buy,
			}
		)

		self.assertEqual (
			Order(
				'',
				Limit(1/3.0),
				Side.Sell,
				0
			),
			{
				'price': {'type':'limit','price':Decimal('0.3333')},
				'sym': '',
				'qty': 0,
				'side': Side.Sell,
			}
		)




class TestEngine ( unittest.TestCase ):

	def test_sym (self):
		eng = Engine()
		for test, correct in [
			('eur','EUR'),
			('blahBlah','BLAHBLAH'),
			('AAAA','AAAA'),
			('','')
		]:
			self.assertEqual(eng.piston(test)().sym, correct)
	
	def test_basic_execution (self):
		sym = 'SPY'
		eng = Engine()

		prices = [
			(15, (100,200,1)),
			(20, (99,1,18)),
			(21, (101,3,42)),
		]

		for price, sizes in prices:
			for quantity in sizes:
				for side in [Side.Buy,Side.Sell]:
					eng.submit(
						Order(
							sym,
							Limit(price),
							side,
							quantity
						)
					)

		txs =  [ { k:v for k,v in tx.items() if k != 'time' } for tx in eng.piston(sym)().txs ]

		# print(txs)
		i = 0
		for price, sizes in prices:
			for qty in sizes:
				self.assertEqual(
					txs[i]['px'],
					Decimal(price)
				)
				self.assertEqual(
					txs[i]['qty'],
					qty
				)
				i += 1
	

	def test_cancel (self):
		sym = 'SPY'
		eng = Engine()
		self.assertEqual ( len(eng.piston(sym)()._manager._orders), 0 )
		o = Order( sym, Limit(100), Side.Sell, 1 )
		orderid = eng.submit(o)

		# print(orderid)

		self.assertEqual ( len(eng.piston(sym)()._manager._orders), 1 )

		# print(eng.status(orderid))

		eng.cancel(orderid)
		self.assertEqual (
			eng.piston(sym)()._manager._orders[orderid]['status'],
			'cancelled'
		)
		self.assertEqual ( len(eng.piston(sym)()._manager._orders), 1 )
	


	def test_partial ( self ):
		"""Ensure that orders are marked as partial correctly
		"""
		# print("Test partial")
		sym = 'SPY'
		eng = Engine()

		orders = [
			Order (
				sym,
				Limit(10),
				Side.Buy,
				10
			),
			Order (
				sym,
				Limit(8),
				Side.Buy,
				10
			),
			Order (
				sym,
				Limit(8),
				Side.Sell,
				12
			),
		]

		# ids = [ eng.submit(o) for o in orders ]
		ids = []
		for o in orders:
			ids.append(eng.submit(o))
			# print(eng.piston(sym)().book)
			# print(eng.status(ids[-1]))


		corrects = [
			{'status': 'filled',  'filled': 10, 'averagepx': Decimal('8.0000')},
			{'status': 'partial', 'filled': 2, 'averagepx': Decimal('8.0000')},
			{'status': 'filled',  'filled': 12, 'averagepx': Decimal('8.0000')},
		]
		
		for oid, valid in zip(ids,corrects):
			self.assertEqual(
				{ k:v for k,v in eng.status(oid).items() if k in ('status','filled','averagepx') },
				valid
			)
	

	def test_market (self):
		"""Test placement of market orders
		"""
		# print("Test market")
		sym = 'SPY'
		eng = Engine()

		orders = [
			Order (
				sym,
				Limit(10),
				Side.Buy,
				10
			),
			Order (
				sym,
				Limit(8),
				Side.Buy,
				10
			),
			Order (
				sym,
				Market(),
				Side.Sell,
				12
			),
		]

		# ids = [ eng.submit(o) for o in orders ]
		ids = []
		for o in orders:
			ids.append(eng.submit(o))
			# print(eng.piston(sym)().book)
			# print(eng.status(ids[-1]))

		corrects = [
			{'status': 'filled',  'filled': 10, 'averagepx': Decimal('10.0000')},
			{'status': 'partial', 'filled': 2, 'averagepx': Decimal('8.0000')},
			{'status': 'filled',  'filled': 12, 'averagepx': Decimal('9.667')},
		]
		
		for oid, valid in zip(ids,corrects):
			self.assertEqual(
				{ k:v for k,v in eng.status(oid).items() if k in ('status','filled','averagepx') },
				valid
			)





class TestLattice ( unittest.TestCase ):
	
	def test_insert (self):
		l = lattice.Lattice()

		# print("testing insert")
		t1 = time.time()
		n = 10*1000
		k = 900
		for i in range(n):
			i = (i ** k) % n
			x = i % k
			y = i // k
			l.insert(x,y,(x,y))
		t2 = time.time()
		print("Lattice Insert: {0:,.0f} loops, {1:.3f} us per insert".format(n*1.0,1000*1000*(t2-t1)/n))

		vals = [ x for x in l ]
		self.assertTrue(
			all(vals[i] <= vals[i+1] for i in range(len(vals) - 1))
		)
	


	def test_get (self):
		l = lattice.Lattice()
		
		vals = [
			(x,y, x*10+y)
			for x in range(100)
			for y in range(10)
		]

		for x,y,z in vals:
			l.insert(x,y,z)

		random.shuffle(vals)

		for x,y,z in vals:
			self.assertEqual(
				l.get(x,y),
				z
			)



	def test_pop (self):
		l = lattice.Lattice()
		
		vals = [
			(x,y, x*10+y)
			for x in range(100)
			for y in range(10)
		]

		for x,y,z in vals:
			l.insert(x,y,z)

		random.shuffle(vals)

		for x,y,z in vals:
			self.assertEqual(
				l.pop(x,y),
				z
			)
		self.assertEqual(0, len(l))




def run():
	return unittest.main()
	


if __name__ == '__main__':
	run()
