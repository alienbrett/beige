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
		self.bins = []




	def _find(self, id1):
		"""Returns tuple (x,y), where:
			x is 0 if id1 is found, or 1 if id1 isn't an item.
			y will be the desired index, or the position to insert a new one
		"""
		y = len(self.bins)
		for i in range(y):
			# print("bin[{0}] vs {1}".format(self.bins[i][0],id1))
			if self.bins[i][0] >= id1:
				if self.bins[i][0] == id1:
					return (0,i)
				else:
					return (1,i)
		return (1,-1)




	def secondLevelInsert(self, whichBin, id2, obj):
		"""Given a bin, and the id2 and obj to insert, do so.
		"""
		ball = [id2,obj]
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

		# Put the metrics at the back of the list
		# Make sure its the right length
		# if len(whichBin) == 2:
		# 	for ballId, ballObj in 
		# 	whichBin.append([])
		# whichBin[
			




	def insert(self, id1, id2, obj):
		"""Inserts (or overwrites) an object with the given ID's
		"""
		x,y = self._find(id1)
		if x == 1:
			# Item was not found
			z = [id1, []]
			if y == -1:
				# Just append to the back of the list
				self.bins.append(z)
			else:
				self.bins.insert(y,z)
		# insert there
		self.secondLevelInsert( self.bins[y], id2, obj )
		



	def __access(self, id1, id2, f, ifNotFound=None):
		x,y = self._find(id1)
		if x == 1:
			return ifNotFound
		else:
			try:
				j = next( i for i,o in enumerate(self.bins[y][1]) if o[0] >= id2 )

				# Now we have the correct version
				if self.bins[y][1][j][0] == id2:

					# Apply the function
					result = f( self.bins[y][1], j)

					# Should we close down this empty bin?
					if len(self.bins[y][1]) == 0:
						self.bins.pop(y)

					# Return the value of f
					return result

			except:
				return ifNotFound



	def pop(self, id1, id2, ifNotFound=None):
		"""Just like get(), but returns actual object and removes it from this data structure.
		"""

		def f (l, pos):
			return l.pop(pos)[1]

		return self.__access(id1, id2, f, ifNotFound)


	
	def __len__(self):
		return sum( len(b[1]) for b in self.bins )





	def get(self, id1, id2, ifNotFound=None):
		"""Returns the object with given ID's.
		Returns ifNotFound object if object isn't part of this data structure.
		"""
		def f (l, pos):
			return l[pos][1]
		return self.__access(id1, id2, f, ifNotFound)
			


	

	def __iter__(self):
		"""Iterate through every object, in order.
		"""
		return LatticeIterator(self.bins)
