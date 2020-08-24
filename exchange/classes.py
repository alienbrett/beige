import time
from enum import Enum
from decimal import *

"""
	Order types:
		1) Limit
		2) Market
"""
class Side(Enum):
	Buy = 1
	Sell = 2

dprec = 4
getcontext().prec = dprec


def Market():
	return {'type':'market'}

def Limit(price:float):
	return {
		'type':'limit',
		'price':Decimal(
			('{:.' + str(dprec) + 'f}').format(price)
		)
	}


def Order ( instrument:str, type_:dict, side:Side, quantity:int, time=None ):

	if time is None:
		time = time.time()
	else:
		time = float(time)

	assert isinstance(instrument,str)
	assert isinstance(type_,dict)
	assert isinstance(side,Side)
	assert isinstance(quantity,int)
	assert isinstance(time, float)
	instrument = instrument.upper()

	return {
		'sym': instrument,
		'price': type_,
		'side': side,
		'qty': quantity,
		'time': time,
	}
