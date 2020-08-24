import weakref



class weaklist(list):
	__slots__=('__weakref__',)



class LatticeIterator:
	def __init__(self, bins):
		self.bins = bins
		self.i = 0
		self.j = 0
	
	def __next__(self):
		if self.i >= len(self.bins):
			raise StopIteration()
		if self.j >= len(self.bins[self.i][1]):
			self.j = 0
			self.i += 1
			return self.__next__()

		x = self.bins[self.i][1][self.j][1]
		self.j += 1
		return x



class Lattice:
	"""Lattice class that should hold 2 tiers of ordering.

	1) Bins, where similar entries are aggregated. Lower bins will appear first.
	2) Balls, an ordered list of objects.

	Inserts of a single object will
		1) Create a corresponding bin (if needed), or find the needed bin
		2) Add the ball to this bin, in the correct sorted order as the others.
	"""
	def __init__(self):
		self.bins = weaklist()


	def _find(self, id1):
		"""Returns tuple (x,y), where:
			x is 0 if id1 is found, or 1 if id1 isn't an item.
			y will be the desired index, or the position to insert a new one
		"""
		x = 1
		y = len(self.bins)
		try:
			y = next( i for i,o in enumerate(self.bins) if o[0] >= id1 )
			if y > id1:
				# We didn't find it
				x = 0
		except:
			# Object wasn't found. Reached end of loop
			x = 0
		return (x,y)


	def secondLevelInsert(self, binRef, id2, obj):
		"""Given a weakref to a bin, and the id2 and obj to insert, do so.
		"""
		ball = [id2,obj]
		whichBin = binRef()
		if whichBin is not None:
			try:
				y = next( i for i,o in enumerate(whichBin[1]) if o[0] >= id2 )
				if whichBin[1][y][0] == id2:
					# Replace the old object with this one
					whichBin[1][y][1] = obj

				# Now insert at this position
				whichBin[1].insert(y, ball)
			except:
				# We can just append at the back
				whichBin[1].append(ball)
		else:
			raise RuntimeException("Weakreference is null!")
			


	def insert(self, id1, id2, obj):
		"""Inserts (or overwrites) an object with the given ID's
		"""
		x,y = self._find(id1)
		if x == 0:
			j = weaklist()
			j.append(id1)
			j.append(weaklist())
			# Item was not found
			# Just append to the back of the list
			self.bins.append(j)
			y = -1

		# Get reference to this bin
		r = weakref.ref( self.bins[y])
		# And insert there
		self.secondLevelInsert( r, id2, obj )
		

	def __access(self, id1, id2, f, ifNotFound=None):
		x,y = self._find(id1)
		if x == 0:
			# print("Not found at top level")
			return ifNotFound
		else:
			# Get reference to the list we want
			whichBin = weakref.ref(self.bins[y])()
			try:
				y = next( i for i,o in enumerate(whichBin[1]) if o[0] >= id2 )

				if whichBin[1][y][0] == id2:
					# Return the object we just found
					return f( whichBin[1][y], 1)

			except:
				return ifNotFound


	def pop(self, id1, id2, ifNotFound=None):
		"""Just like get(), but returns actual object and removes it from this data structure.
		"""
		return self.__access(id1, id2, list.pop, ifNotFound)
	


	def get(self, id1, id2, ifNotFound=None):
		"""Returns the object with given ID's.
		Returns ifNotFound object if object isn't part of this data structure.
		"""
		def f (l, pos):
			return l[pos]
		return self.__access(id1, id2, f, ifNotFound)
			


	

	def __iter__(self):
		"""Iterate through every object, in order.
		"""
		return LatticeIterator(self.bins)
