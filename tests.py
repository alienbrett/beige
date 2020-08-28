import unittest
import numpy as np
from tqdm import tqdm
import time
import sys
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
				entity='a',
			),
			{
				'price': {'type':'market'},
				'sym': 'SPY',
				'qty': 100,
				'side': Side.Buy,
				'acct': 'A'
			}
		)

		self.assertEqual (
			Order(
				'',
				Limit(1/3.0),
				Side.Sell,
				0,
				entity='',
			),
			{
				'price': {'type':'limit','price':Decimal('0.3333')},
				'sym': '',
				'qty': 0,
				'side': Side.Sell,
				'acct': ''
			}
		)



class TestAccountManager ( unittest.TestCase ):
	def test_add ( self ):
		'''Can we move assets into and out of an account correctly
		'''
		act = AccountManager()

		# Give him 10 dollars to start
		act.init('meme', {'$': 10})

		for sym, qty, px, correct in (

			# Buy 10 SPY for $1 a piece
			('spy', 10, 1.0, np.array([0, 10])),

			# Short 99 AMD for $8 a piece
			('amd', -99, 8, np.array([792.0, -99.0, 10.0])),

			# Buy 10 AMD for 0.0
			('amd', 10, 0, np.array([792.0, -89.0, 10.0])),

		):
			act.tx('meme', sym, qty, px)

			self.assertTrue(
				np.all( act.df.values == correct )
			)
	


	def test_tx ( self ):
		"""Do assets actually flow between accounts correctly
		"""

		act = AccountManager()

		# Give him 10 dollars to start
		act.init('uncle sam', {'$': -100*100, 'roads': 100, 'social security': 2})
		act.init('tax payer', {'$': 10})

		for sym, qty, px, correct in (

			# Tax the taxpayer $3, but give him 1 roads
			('roads', 1, 3, np.array([[-9997, 99, 2], [7, 1, 0]])),

			# Tax the taxpayer $5, but give him 5 social securities
			('social security', 5, 1, np.array([[-9992, 99, -3], [2, 1, 5]])),
		):
			act.exchange (
				'tax payer',
				'uncle sam',
				sym, qty, px
			)
			# print(act.df)
			# print(act.df.values)

			self.assertTrue(
				np.all( act.df.values == correct )
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
							quantity,
							entity=('A' if side == Side.Buy else 'B'),
						)
					)

		txs =  [ { k:v for k,v in tx.items() if k != 'time' } for tx in eng.piston(sym)().txs ]
		# print(eng.accounts.df)

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
		o = Order( sym, Limit(100), Side.Sell, 1, entity='A' )
		orderid = eng.submit(o)

		self.assertEqual ( len(eng.piston(sym)()._manager._orders), 1 )

		eng.cancel(orderid)
		self.assertEqual (
			eng.status(orderid)['status'],
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
				10,
				entity='A',
			),
			Order (
				sym,
				Limit(8),
				Side.Buy,
				10,
				entity='A',
			),
			Order (
				sym,
				Limit(8),
				Side.Sell,
				12,
				entity='B',
			),
		]

		# ids = [ eng.submit(o) for o in orders ]
		ids = []
		for o in orders:
			ids.append(eng.submit(o))


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
				10,
				entity='A',
			),
			Order (
				sym,
				Limit(8),
				Side.Buy,
				10,
				entity='A',
			),
			Order (
				sym,
				Market(),
				Side.Sell,
				12,
				entity='B',
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
	


def speed(profile=False):
		
	eng = Engine()
	syms = ['spy','tsla','amd','gld','tax','blah','what?','gold','moon','ba','xxx']
	nOrders = 8*1000
	pctMarket = 0.2
	verbose=False

	import random
	random.seed(0)

	caps, orders = simulate.orderGen(
		syms,
		nOrders,
		pctMarket,
		useCaps = True
	)

	# Submit all market-maker orders
	for o in caps:
		eng.submit(o)

	print("Starting engine")


	def f():
		t1 = time.time()

		for o in orders:
			bid, ask, last, _, _, _ = eng.quote(o['sym'])
			mid = (bid+ask)/Decimal(2)
			if last is None:
				px = mid
			else:
				px = last
			try:
				o['price']['price'] += px
			except:
				pass
			eng.submit(o)
			if verbose:
				print(o)
				print(eng.quotes)
				print()

		t2 = time.time()
		print("Done. Processed {0} orders in {1:.2f}s, {2:.2f}us each".format(
			nOrders,
			(t2 - t1),
			1000* 1000 * (t2 - t1) / nOrders
		))

		# return t2,t1
	
	if profile:
		import cProfile
		import pstats
		with cProfile.Profile() as pr:
			f()
		ps = pstats.Stats(pr).sort_stats('time')
		ps.print_stats()
	else:
		f()

		print("TRANSACTIONS:")
		print(eng.txs)

		print("QUOTES:")
		print(eng.quotes)

		print("ENDING ACCOUNT HOLDINGS")
		print(eng.accounts.df)
		

	


if __name__ == '__main__':

	# Run the standard stuff
	if len(sys.argv) == 1:
		run()
	# Run the performance tests
	elif len(sys.argv) == 2:
		if sys.argv[1] == 'speed':
			speed()
		elif sys.argv[1] == 'profile':
			speed(profile=True)
