class TableData():
	'''
	This class is used to hold data which the template renders inserts into
	listing tables.
	'''
	def __init__(self,cols,data_sets):
		#logger.info('TableData.__init__: {} - {}'.format(cols, data_sets))

		# validate and store the columns
		assert type(cols) is list, 'cols must be a list'
		assert type(data_sets) is list, 'data_set must be a list'
		self.cols = cols

		# Instantiate our attributes to populate
		self.names = {}
		self.data_points = {}

		# Breakdown the datapoints and set values
		num_key = 0
		for data_set in data_sets:
			name = data_set.pop('name')
			self.names[str(num_key)] = name
			self.data_points[str(num_key)] = data_set

			# Let's just manually add the
			if ('episode' in self.data_points[str(num_key)]):
				self.data_points[str(num_key)]['link'] = 'episode/{}'.format(self.data_points[str(num_key)]['episode'])
			else:
				self.data_points[str(num_key)]['link'] = '{}'.format(self.data_points[str(num_key)]['id'])

			num_key += 1

		#logger.info('INITIALIZED: {}'.format(self.tmp_repr()))

	def __str__(self):
		return str({
			'names': self.names,
			'data_points': self.data_points,
		})

	def tmp_repr(self):
		return str({
			'cols': self.cols,
			'names': self.names,
			'data_points': self.data_points,
		})

	def get_columns(self):
		return self.cols

	def get_names(self):
		return self.names

	def get_name(self, num_key):
		return self.names[str(num_key)]

	def get_data_points(self,num_key):
		return self.data_points[str(num_key)]

	def get_data_point(self,num_key,data_point):
		return self.data_points[str(num_key)][data_point]

	def get_row_data_points(self,num_key):
		return [self.get_data_points(str(num_key))[x] for x in self.get_data_points(str(num_key)) if x in self.cols]
