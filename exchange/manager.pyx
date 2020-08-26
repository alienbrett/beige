import time



class OrderManager:

	def __init__(self):
		self._orders = {}
	
	def get(self, orderid):
		"""Get's a copy of the order
		"""
		return self._orders.get(orderid,None)

	def put(self, orderid, order):
		"""Puts the order into our storage
		"""
		self._orders[orderid] = order
	

	def add(self, orderid, order):
		"""Add a new order
		"""
		# Initialize
		order['submitted'] = time.time()
		order['filled'] = 0
		order['averagepx'] = 0
		order['filledtime'] = None
		order['status'] = 'open'

		self.put(orderid, order)


	
	def fill(self, orderid, px, qty):
		"""Fills an order, partially or completely
		Returns True if the order is still outstanding after this fill.
		"""
		o = self.get(orderid)
		# Some checks
		if o is None:
			raise ValueError("Order ID supplied does not exist")
		if o['status'] == 'filled':
			raise ValueError("Order cannot be filled- it is already completed")
		if o['status'] == 'cancelled':
			raise ValueError("Order cannot be filled- it was previously cancelled")

		# Calculate new info about order
		remaining = o['qty'] - o['filled']
		newqty = o['qty'] + qty
		o['averagepx'] = (o['averagepx'] * o['filled'] + qty * px) / newqty
		o['filled'] = newqty
		o['filledtime'] = time.time()

		result = None
		# Test whether this order is done
		if newqty < o['qty']:
			# Still open
			o['status'] = 'partial'
			result = True
		else:
			# Order is filled fully
			o['status'] = 'filled'
			result = False

		# Add it back to the storage
		self.put(orderid, o)
		return result


	def cancel(self, orderid):
		"""Cancel's an order
		"""
		o = self.get(orderid)
		o['status'] = 'cancelled'

		self.put(orderid,o)
