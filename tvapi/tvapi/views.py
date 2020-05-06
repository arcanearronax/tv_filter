from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.views import View
from django.template import loader
from django.shortcuts import redirect, reverse
from django.urls.exceptions import Resolver404
from .forms import *
from .models import Show, Episode, Cast, ShowException, EpisodeException, CastException, site_scraper
from .redactions import words
from .table_data import TableData
import logging
import time

logger = logging.getLogger('viewlog')

class APIView(View):

	key_args = ['show_id', 'season', 'episode']

	# Decorator to validate inputs


	@classmethod
	def generate_table_data(cls,data_rows,data_sets):
		'''
		This receives a list populated by single layer dictionaries and creates
		a table_data object used to generate a table for the webpage.
		The dictionaries in the list must include identical keys.
		'''
		data_entries = []
		# Loop over the data sets we have
		for data_set in data_sets:
			# Look at each element in the data set
			data_entry = {'name': data_set.pop('name')}
			data_entry['data_points'] = data_set

			data_entries.append(data_entry)

		# Construct the table_data dict to return
		table_data = {
			'cols': data_rows,
			'entries': data_entries,
		}

		#logger.info('table_data: {}'.format(table_data))
		return table_data

	def get_db_search_results(self,request):
		'''
		This method returns a context dictionary used to populate the basic
		search page.
		'''
		logger.info('APIView.get_db_search_results')
		context = {
			'form': SearchForm,
			'page_header': 'Search for a show',
		}

		return context

	def get_imdb_search_results(self,request,search_term):
		'''
		This is used to return a search result page which displays IMDB search
		results for a user provided search.
		'''
		logger.info('APIView.get_imdb_search_results: {}'.format(search_term))

		# This is mostly a temporary measure
		# We don't want to log everything that comes up as a search result
		search_results = site_scraper.get_imdb_title_search(search_term)
		logger.info('	Got search results: {}'.format(len(search_results)))

		converted_search_results = [
			{
				'name': x['imdb_name'],
				'year': x['year'],
				'id': x['imdb_id'],
			} for x in search_results
		]
		# Need to convert search results to a TableData object
		table_data = TableData(['name', 'year'], converted_search_results)


		logger.info('CONVERTED: {}'.format(str(table_data)))

		return {
			'name': 'name',
			'page_header': 'Search Results',
			'sub_header': 'Go Back to Search',
			'sub_header_link': '/',
			'name_col_alt': 'search results',
			'form': SearchForm,
			'table_data': table_data,
		}

	def get_recent_shows(self,request):
		'''
		This is used to resturn a context dictionary to populate a show listings
		page with shows to populate the page.
		'''
		logger.info('APIView.get_recent_shows:')

		recent_shows = Show.get_shows()
		# Parse out the data we want in the listing table
		show_data = []
		for show in recent_shows:
			show_data.append({
				'name': show.imdb_name,
				'year': show.year,
				'id': show.show_id,
			})

		context = {
			'page_header': 'Show Index',
			'sub_header': 'Go to Show Search',
			'sub_header_link': '../',
			'table_data': TableData(['name','year'],show_data),
		}

		return context

	#@validate_inputs
	def get_show_page(self,request,show_id):
		'''
		This is used to return a context dictionary which contains information
		about a show used to populate the page.
		'''
		logger.info('APIView.get_show_page: {}'.format(show_id))

		show_name = Show.get_show_name(show_id)
		seasons = Show.get_season_count(show_id=show_id)
		show_season_data = []
		for season in range(1, seasons+1):
			show_season_data.append({
				'name': season,
				'name_col_alt': 'season',
				'id': 'season/{}'.format(season),
			})

		context = {
			'page_header': show_name,
			'sub_header': 'Go to Show Index',
			'sub_header_link': '../',
			'table_data': TableData(['name'], show_season_data),
		}

		return context

	def get_season_page(self,request,show_id,season):
		'''
		This method is called by get and returns a context dictionary used to
		populate the template selected by the get method. The context dictionary
		is populated with information about the show's season. The template to
		fill out with the context dictionary is selected in the get method.
		'''
		logger.info('APIView.get_show_page: {} - {}'.format(show_id,season))

		# This doesn't feel right...
		def get_cast_match(words,episode_id):
			'''
			This method returns True if a match to a restricted word is found.
			If a match is not found, it returns False.
			'''
			match_found = False

			for word in words:
				match_found = (Cast.get_match(episode_id,word) or match_found)
				if match_found:
					break

			return match_found

		# Try to get the episodes in the season
		# Not catching ShowException here, generate 404 response in get
		episodes = Episode.get_count(show_id,season=season)

		show_name = Show.get_show_name(show_id)
		season_episode_data = [
			{
				'id': episode['episode_id'],
				'episode': episode['ep_num'],
				'name': episode['ep_name'],
				'match_found': get_cast_match(words,episode['episode_id']),
			}	for episode in Episode.get_episodes(show_id,season,cast=True)
		]
		logger.info('	found episodes: {}'.format(episodes))

		context = {
			'page_header': show_name,
			'page_header_link': '../../../{}'.format(show_id),
			'sub_header': 'Season {}'.format(season),
			'table_data': TableData(['episode','name','match_found'], season_episode_data)
		}

		return context

	#@validate_inputs
	def get_episode_page(self,request,show_id,season,episode):
		'''
		This is used to return a context dictionary used to populate the page
		for an episode, including the match_found flag.
		'''
		logger.info('APIView.get_episode_page: {} - {} - {}'.format(show_id,season,episode))

		# Try to find the episode
		try:
			# We should probably just grab the episode as a var
			episode_id = Episode.get_episode_id(show_id=show_id,season=season,ep_num=episode)
			context = {}

		except EpisodeException as ee:
			raise Http404('Failed to find episode: {}'.format(ee))
		# If we don't find the episode, return a warning
		except IndexError as i:
			logger.error('get_episode_page index_error: {}'.format(i))
			warning = 'Episode does not exist: {}'.format(episode)
			#return self.get(request,show_id,season=season,warning=message)
			show_name = Show.get_show_name(show_id)
			context = {
				'show_name': show_name,
				'page_header': show_name,
				'page_header_link': "/tv/{}".format(show_id),
				'form': EpisodeForm,
				'show_id': show_id,
				'season': season,
			}

		# If we have a different issue, return a warning
		except ValueError as v:
			logger.error('get_episode_page value_error: {}'.format(v))

			show_name = Show.get_show_name(show_id)
			context = {
				'show_name': show_name,
				'page_header': show_name,
				'page_header_link': "/tv/{}".format(show_id),
				'form': EpisodeForm,
				'show_id': show_id,
				'season': season,
			}

		# Return a message if we get an unknown exception
		except Exception as e:
			logger.error('get_episode_page exception: {}'.format(e))

			show_name = Show.get_show_name(show_id)
			context = {
				'show_name': show_name,
				'page_header': show_name,
				'page_header_link': "/tv/{}".format(show_id),
				'form': EpisodeForm,
				'show_id': show_id,
				'season': season,
			}

		# If we found the episode, check for cast matches
		else:
			match = False

			try: # Loop over the cast, looking for a match
				for term in words:
					match = (Cast.get_match(episode_id,term) or match)

				if match:
					context.update({
						'message': 'Match Found',
					})
				else:
					context.update({
						'message': 'No Match Found',
					})

			# If we failed to retrieve the cast, return the error
			except CastException as c:
				context.update({
					'match_error': str(c),
				})

			# Look for the show's name
			try:
				show_name = Show.get_show_name(show_id)
				context.update({
					'show_name': show_name,
					'form': EpisodeForm,
					'show_id': show_id,
					'season': season,
					'episode': '{} - {}'.format(episode, Episode.get_name(show_id=show_id,season=season,ep_num=episode)),
					'match': match,
					'page_header': show_name,
					'page_header_link': "/tv/{}".format(show_id),
				})

			# If we fail to retrieve the show's page, do something...
			except InvalidPage as i:
				show_name = Show.get_show_name(show_id)
				context.update({
					'show_name': show_name,
					'form': EpisodeForm,
					'show_id': show_id,
					'season': season,
					'match': match,
					'page_header': show_name,
					'page_header_link': "/tv/{}".format(show_id),
				})

		return context

	@classmethod
	def get_404_page(cls,request, exception=None):
		logger.info('APIView.get_404_page: {}'.format(exception))
		logger.info('APIView.get_404_page: {}'.format(type(exception)))
		template = loader.get_template('404.html')

		# If the user followed a bad link, get previous page
		logger.info(request.META)
		try:
			sub_header = 'Please try a different URL'
			sub_header_link = ''
		except Exception as e:
			logger.info('404_error: {}'.format(e))
			sub_header = 'Go to Page Search'
			sub_header_link = reverse('shows')

		logger.info('Do we get here?')

		if type(exception) is Resolver404:
			logger.info('WE ACTUALLY GOT HERE')
			page_header = 'URL is Invalid'
			error_message = 'Please try a different URL'
		elif type(exception) is ShowException:
			logger.info('1234567')
			page_header = 'Show Error'
			error_message = exception
		elif type(exception) is SeasonException:
			logger.info('98765432')
			page_header = 'Season Error'
			error_message = exception
		elif type(exception) is EpisodeException:
			logger.info('abcdefg')
			page_header = 'Episode Error'
			error_message = exception
		elif type(exception) is Http404:
			logger.info('GOT HTTP404')
			page_header = 'DOES THIS WORK?'
			error_message = 'maybe'
		else:
			logger.info('WE GOT HERE')
			page_header = exception
			error_message = exception

		context = {
			'page_header': page_header,
			'sub_header': sub_header,
			'sub_header_link': sub_header_link,
			'error_message': error_message,
		}
		logger.info('APIView.get_404_page context: {}'.format(context))
		return HttpResponseNotFound(template.render(context,request))

	@classmethod
	def get_500_page(cls, request):
		logger.info('APIView.get_500_page')
		template = loader.get_template('500.html')

		# If the user followed a bad link, get previous page
		if request.META.get('HTTP_REFERER'):
			sub_header = 'Go back...'
			sub_header_link = request.META.get('HTTP_REFERER')
		else:
			sub_header = 'Go to Page Search'
			sub_header_link = reverse('shows')

		context = {
			'page_header': 'Server Error',
			'sub_header': sub_header,
			'sub_header_link': sub_header_link,
			'error_message': 'Unknown Error',
		}
		logger.info('APIView.get_500_page context: {}'.format(context))
		return HttpResponseServerError(template.render(context,request))

	def get(self, request, **kwargs):
		'''
		This is used to respond to any GET requests directed towards this class.
		It identifies the template and context dictionary used to render a
		response to the request.
		'''
		req_path = request.path_info
		logger.info('APIView.get: {} - {}'.format(req_path, kwargs))

		# Need to unpack our args
		try:
			show_id = int(kwargs['show_id'])
		except KeyError as k:
			show_id = None

		try:
			season = int(kwargs['season'])
		except KeyError as k:
			season = None

		try:
			episode = int(kwargs['episode'])
		except KeyError as k:
			episode = None

		try:
			search_id = kwargs['search_id']
		except KeyError as k:
			search_id = None

		try:
			search_term = kwargs['search_term']
		except KeyError as k:
			search_term = None

		# This is used to return a show's page based on imdb_id
		if search_id:
			template_name = 'listing.html'
			try:
				show_id = Show.get_show_by_imdb_id(search_id).show_id
			except ShowException as se:
				raise Http404(se)
			except Exception as e:
				raise Http404(e)
			else:
				return redirect('showView',show_id=show_id) # Just redirect instead

		# Look for an episode's page
		elif episode:
			template_name = 'info.html'
			context = self.get_episode_page(request, **kwargs)

		# Look for a season's page
		elif season:
			template_name = 'listing.html'
			try:
				context = self.get_season_page(request, **kwargs)
			except Exception as se:
				logger.error('Failed to find season: {}'.format(se))
				raise Http404('Season does not exist, is this rendering right?')

		# We're looking for a show
		elif (request.path_info[0:4] == '/tv/'):

			# We return the show's page
			if show_id:
				template_name = 'listing.html'
				# Try to get info about the requested show
				try:
					context = self.get_show_page(request, **kwargs)
				# Failed to find a given show
				except ShowException as se:
					logger.info('NEW EXCEPTION: {}'.format(se))
					raise Http404(se)
				# Some other exception
				except Exception as e:
					#raise Http500('Unknown Error: {}'.format(e))
					raise Http404(e)

			# We return the recent shows page
			else:
				template_name = 'listing.html'
				context = self.get_recent_shows(request)

		# Look for a search result page
		elif search_term:
			template_name = 'listing.html'
			context = self.get_imdb_search_results(request, **kwargs)

		# Just return the search page
		else:
			template_name = 'query.html'
			context = self.get_db_search_results(request)

		# Render and return the response
		template = loader.get_template(template_name)
		return HttpResponse(template.render(context,request))

	# This is used to return to user searches
	def post(self,request,show_id=None,season=None,episode=None):
		'''
		This is used to respond to POST requests
		'''
		logger.info('APIView.post - {} - {} - {}'.format(show_id,season,episode))
		template = loader.get_template('query.html')
		form = PostForm(request.POST)

		# Need to verify the submitted form is valid
		if form.is_valid():
			# Get our search type and term
			queryvalue = form.cleaned_data['queryvalue']
			logger.info('\tform_validated: {}'.format(queryvalue))

			#ret = None
			#if querytype == 'search':
			ret = self.get(request,search_term=queryvalue)
			# Change this to a redirect later?


		# If the form isn't invalid, log the errors and
		else:
			logger.info('\tFORM INVALID')
			logger.info('\t{}'.format(form.errors))

		return ret
