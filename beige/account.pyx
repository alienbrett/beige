import weakref


class AccountManager:
	def __init__(self):
		self.accounts = {}

	@property
	def ref(self):
		return weakref.ref(self)


	def modify(self, account:str, symbol:str, qty:float):
		"""Add shares of symbol to an account.

		Transactions should be two modifies- one for $, one for the other item
		"""
		symbol = symbol.upper()
		j = self.accounts.get(account,{})
		j[symbol] = j.get(symbol,0) + qty
		self.accounts[account] = j
		return j


	
	def tx(self, account:str, symbol:str, qty:float, unitPx:float):
		"""Exchange qty shares of symbol, for unitPx each.
		Changes '$' by the opposite sign of this quantity.
		"""
		account = account.upper()
		self.modify(account, symbol, qty)
		self.modify(account, '$', -1 * qty * unitPx)
	

	def init(self, account:str, holdings:dict):
		"""Initialize an account with some set of holdings.
		"""
		account = account.upper()
		for k, v in holdings.items():
			self.modify( account, k, v )


	def exchange ( self, buyer:str, seller:str, symbol:str, qty:float, unitPx:float ):
		# Update the accounts
		buyer = buyer.upper()
		seller = seller.upper()
		for entity, modifier in ( (buyer, 1), (seller, -1) ):
			self.tx(
				account = entity,
				symbol  = symbol,
				qty     = qty * modifier,
				unitPx  = unitPx
			)


	@property
	def df(self):
		import pandas as pd
		df = pd.DataFrame.from_records(
			data = list(self.accounts.values()),
			index = list(self.accounts.keys())
		)
		# Get assets in an aggreable ordering
		df = df[ ['$'] + sorted([ x for x in df.columns if x != '$' ])]
		df = df.fillna(0)
		return df



