# Python native Exchange engine

![Website](https://img.shields.io/website?up_message=up&url=https%3A%2F%2Fgithub.com%2Falienbrett%2Fbeige%2F)![PyPI](https://img.shields.io/pypi/v/beige)![PyPI - License](https://img.shields.io/pypi/l/beige)![GitHub issues](https://img.shields.io/github/issues/alienbrett/beige)

### Beige

Why Beige?

Because it's not particularly attractive,
there's probably a better color out there,
but it kinda works.
I was surprised that there is no package existing with the name ```beige``` yet!


### A simple, slow, exchange library

Beige is a pretty simple library that provides the full functionality of a matching engine, with features for tracking account balances and ongoing quote.

### Example

Import the right bits, and spin up the engine
```python
from beige import Engine, Order, Market, Limit, Side

# Create the engine
eng = Engine()
```

Account balances can be initialized at the start of the market session
```python
# Start a person off with some given account balance
eng.accounts.init('person-a', {'$':100.01, 'TSLA':1})

# Person is missing 1 dollar, and owns 10 'what?'
eng.accounts.init('person-b', {'$':-1, 'what?':10})
```

Then orders can be submitted in a fairly intuitive way:
```python
# Limit buy order for 'what?' security, 1
# Store the ID, and we can query its status later
oid = eng.submit(
  Order(
    instrument = 'what?',
    type_ = Limit(10),
    side = Side.Sell,
    quantity = 5,
    entity = 'person-b',
  )
)

# Submit a market order that
eng.submit(
  Order(
    'WHAT?',
    Market(),
    Side.Buy,
    1,
    'person-a',
  )
)
```
Once the ID for an order has been retrieved, we can see the full information on the order at any time:
```python
o = eng.status(oid)
# type(o) == dict
# o.keys() == ['sym','price','side','qty','acct','id','submitted','filled','averagepx','filledtime','status']
```


A full chronological transaction dataset is available
```python
df = eng.txs
# df.columns = ['qty','px','time','sym']
```

At any point, a quote can be requested.
Note that `None` will be returned for any value that isn't available, for example, `last` will be empty if no transactions have taken place yet.
```python
bid, ask, last, bidsize, asksize, lastsize = eng.quote('TSLA')
```



### Limitations

* Speed. The software hasn't been fully optimized and many of the data structures could really benefit from a bit of love and care.
* Integer-only quantities
* All account entities and securities are case insensitive, and will be displayed in all caps
* the "$" security encodes cash, and is the base unit for all security transactions. Sorry ex-USA users!


### Testing

* Correctness => ```python3 tests.py```
* Speed => ```python3 tests.py speed```
* Profiler => ```python3 tests.py profile```

I'm averaging about 0.15 ms per order execution.
This works in the sequential market I'm working on, but this may be orders of magnitude slower than needed in your use case.
Feel free to improve the speed, but please pull request back to me.
