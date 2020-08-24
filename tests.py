import unittest
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
		self.assertEqual (
			Order(
				'spy',
				Market(),
				Side.Buy,
				100,
				time=0,
			),
			{
				'price': {'type':'market'},
				'sym': 'SPY',
				'qty': 100,
				'side': Side.Buy,
				'time': 0,
			}
		)

		self.assertEqual (
			Order(
				'',
				Limit(1/3.0),
				Side.Sell,
				0,
				time=0,
			),
			{
				'price': {'type':'limit','price':Decimal('0.3333')},
				'sym': '',
				'qty': 0,
				'side': Side.Sell,
				'time': 0,
			}
		)




class TestPistons ( unittest.TestCase ):

	def test_sym (self):
		for test, correct in [
			('eur','EUR'),
			('blahBlah','BLAHBLAH'),
			('AAAA','AAAA'),
			('','')
		]:
			p = Piston(test)
			self.assertEqual(p.sym, correct)
	





def run():
	return unittest.main()
	


if __name__ == '__main__':
	run()
