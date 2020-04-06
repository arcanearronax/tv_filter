from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views import View
from django.template import loader
from django.shortcuts import redirect, reverse
from .forms import *
from .models import *
from .redactions import words
import logging
import time
from .api_service import *

logger = logging.getLogger('apilog')

class APIView(View):

	# Decorator to validate inputs
	def validate_inputs(func):
		'''
		This is a decorator used to validate the tv, season, and episode
		values passed to GET requests.
		'''
		def wrapper(*args,**kwargs):
			logger.info('validating inputs')

			logger.info('VALIDATE_ARGS: {}'.format(len(args)))

			show_id = args[2]
			season = args[3]
			episode = args[4]

			# Raise an error or passes
			def validate_show_id(show_id):
				'''
				This is used to validate the show_id, if present.
				'''
				logger.info('\tvalidate_show_id: {}'.format(show_id))
				try:
					int(show_id)
					logger.info('\tvalid show_id')
					return True
				except ValueError as v:
					logger.info('\tvalue_error: {}'.format(v))
					raise InvalidShowId(value=show_id,message='Not an int - show_id')
				except TypeError as t:
					logger.info('\ttype_error: {}'.format(t))
					raise InvalidShowId(value=show_id,message='Not an int - show_id')

				return False

			def validate_season(season):
				'''
				This is used to validate the season, if present.
				'''
				try:
					int(season)
					return True
				except ValueError:
					raise InvalidSeason(value=season,message='Not an int - season')

				return False

			def validate_episode(episode):
				'''
				This is used to validate the episode_id, if present.
				'''
				try:
					int(episode)
					return True
				except ValueError:
					raise InvalidInput(value=episode,message='Not an int - show_id')

				return False

			# Make sure we aren't missing an arg
			if (show_id in ('None',None)) and (season not in ('None',None) or episode not in ('None',None)):
				raise InvalidShowId(value=show_id,message='Invalid show_id')

			elif (season in ('None',None)) and (episode not in ('None',None)):
				raise InvalidSeason(value=season,message='Invalid show_id')

			# Make sure the values are valid ints
			valid = True
			if (show_id not in ('None',None)):
				if (not validate_show_id(show_id)):
					raise InvalidShowId(value=show_id,message='Invalid show_id')
			elif (season not in ('None',None)):
				if (not validate_season(show_id)):
					raise InvalidSeason(value=season,message='Invalid season')
			elif (episode not in ('None',None)):
				if (not validate_episode(show_id)):
					raise InvalidEpisode(value=episode,message='Invalid episode')

			return func(*args,**kwargs)

		return wrapper

	def get_search_page(self,request,message=None,warning=None,error=None):
		'''
		This method returns a context dictionary used to populate the basic
		search page.
		'''
		logger.info('APIView.get_show: {} - {} - {}'.format(message,warning,error))
		context = {
			'message': message,
			'warning': warning,
			'error': error,
			'form': SearchForm,
			'page_h1': 'Search for a show'
		}

		return context

	def get_imdb_search(self,request,search_term,message=None,warning=None,error=None):
		'''
		This is used to return a search result page which displays IMDB search
		results for a user provided search.
		'''
		logger.info('APIView.get_imdb_search: {} - {} - {} - {}'.format(search_term,message,warning,error))
		tmpApi = APIService()
		search_results = tmpApi.get_imdb_title_search(search_term)
		logger.info('Got search results: {}'.format(len(search_results)))
		return {
			'message': message,
			'warning': warning,
			'error': error,
			'form': SearchForm,
			'page_h1': 'Search Results',
			'search_results': search_results
		}

	def get_show_listing(self,request,message=None,warning=None,error=None):
		'''
		This is used to resturn a context dictionary to populate a show listings
		page with shows to populate the page.
		'''
		shows = Show.get_shows()
		show_info = {
			'message': message,
			'warning': warning,
			'error': error,
			'form': SearchForm,
			'page_h1': 'Recently Found Shows',
			'shows': [{
				'show_id': show.show_id,
				'show_name': show.imdb_name,
				'imdb_id': show.imdb_id,
				'year': show.year,
			} for show in shows]
		}

		logger.info('SHOW_INFO::: {}'.format(show_info))
		return show_info

	#@validate_inputs
	def get_show_page(self,request,show_id,message=None,warning=None,error=None):
		'''
		This is used to return a context dictionary which contains information
		about a show used to populate the page.
		'''
		logger.info('APIView.get_show_page: {} - {} - {} - {}'.format(show_id,message,warning,error))

		show_name = Show.get_show_name(show_id)
		context = {
			'message': message,
			'warning': warning,
			'error': error,
			'show_name': show_name,
			'form': SeasonForm,
			'show_id': show_id,
			'seasons': [i+1 for i in range(Show.get_season_count(show_id))],
			'page_h1': show_name,
			'page_h1_link': "/tv/{}".format(show_id),
		}

		return context


	def get_season_page(self,request,show_id,season,message=None,warning=None,error=None):
		'''
		This method is called by get and returns a context dictionary used to
		populate the template selected by the get method. The context dictionary
		is populated with information about the show's season. The template to
		fill out with the context dictionary is selected in the get method.
		'''
		logger.info('APIView.get_show_page: {} - {} - {} - {} - {}'.format(show_id,season,message,warning,error))

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

		try: # Get the episode count for the season
			episodes = Episode.get_count(show_id,season=season)

		except Exception as e: # Failed to retrieve episodes
			warning = 'Season does not exist: {}'.format(season)
			logger.info('APIView.get_show_page exception: {}'.format(e))

			show_name = Show.get_show_name(show_id)
			context = {
				'message': message,
				'warning': warning,
				'error': error,
				'show_id': show_id,
				'show_name': show_name,
				'form': SeasonForm,
				'episode_count': Episode.get_count(show_id=show_id,season=season),
				'page_h1': show_name,
				'page_h1_link': "/tv/{}".format(show_id),
			}

		else:
			show_name = Show.get_show_name(show_id)
			episodes = [
				{
					'ep_num': episode['ep_num'],
					'ep_name': episode['ep_name'],
					'match_found': get_cast_match(words,episode['episode_id']),
					'cast': episode['cast'],
				}	for episode in Episode.get_episodes(show_id,season,cast=True)
			]
			logger.info('Episode.get_season_page - episodes: {}'.format(episodes))
			context = {
				'message': message,
				'warning': warning,
				'error': error,
				'show_id': show_id,
				'show_name': show_name,
				'form': EpisodeForm,
				'season': season,
				'episodes': episodes,
				'page_h1': show_name,
				'page_h1_link': "/tv/{}".format(show_id),
			}

		return context

	#@validate_inputs
	def get_episode_page(self,request,show_id,season,episode,message=None,warning=None,error=None):
		'''
		This is used to return a context dictionary used to populate the page
		for an episode, including the match_found flag.
		'''
		logger.info('APIView.get_episode_page: {} - {} - {} - {} - {} - {}'.format(show_id,season,episode,message,warning,error))

		context = {}

		try: # Look for the episode
			# We should probably just grab the episode as a var
			episode_id = Episode.get_episode_id(show_id=show_id,season=season,ep_num=episode)

		except IndexError as i:
			logger.info('IndexError: {}'.format(i))
			warning = 'Episode does not exist: {}'.format(episode)
			#return self.get(request,show_id,season=season,warning=message)
			show_name = Show.get_show_name(show_id)
			context = {
				'show_name': show_name,
				'page_h1': show_name,
				'page_h1_link': "/tv/{}".format(show_id),
				'form': EpisodeForm,
				'show_id': show_id,
				'season': season,
				'warning': warning,
			}

		except ValueError as v:
			logger.info('ValueError: {}'.format(v))
			warning = 'Episode is invalid: {}'.format(episode)

			show_name = Show.get_show_name(show_id)
			context = {
				'show_name': show_name,
				'page_h1': show_name,
				'page_h1_link': "/tv/{}".format(show_id),
				'form': EpisodeForm,
				'show_id': show_id,
				'season': season,
				'warning': warning,
			}

			#return self.get(request,show_id,season=season,warning=warning)

		except Exception as e:
			logger.info('Exception-here: {}'.format(e.__class__.__name__))
			message = 'Unknown Exception: {}'.format(episode)

			show_name = Show.get_show_name(show_id)
			context = {
				'show_name': show_name,
				'page_h1': show_name,
				'page_h1_link': "/tv/{}".format(show_id),
				'form': EpisodeForm,
				'show_id': show_id,
				'season': season,
				'warning': warning,
			}

			#return self.get(request,show_id,season=season,message=message)

		else: # Found the episode, get the cast info
			logger.info('Continuing to process')
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

			except CastException as c: # We fail to retrieve ep cast
				context.update({
					'match_error': str(c),
				})

			try:
				show_name = Show.get_show_name(show_id)
				context.update({
					'show_name': show_name,
					'form': EpisodeForm,
					'show_id': show_id,
					'season': season,
					'episode': '{} - {}'.format(episode, Episode.get_name(show_id=show_id,season=season,ep_num=episode)),
					'match': match,
					'page_h1': show_name,
					'page_h1_link': "/tv/{}".format(show_id),
				})
			except InvalidPage as i:
				show_name = Show.get_show_name(show_id)
				context.update({
					'show_name': show_name,
					'form': EpisodeForm,
					'show_id': show_id,
					'season': season,
					'warning': i,
					'match': match,
					'page_h1': show_name,
					'page_h1_link': "/tv/{}".format(show_id),
				})

		return context


	def get(self,request,search_term=None,show_id=None,season=None,episode=None,message=None,warning=None,error=None,search_id=None):
		'''
		This is used to respond to any GET requests directed towards this class.
		It identifies the template and context dictionary used to render a
		response to the request.
		'''
		logger.info('APIView.get: {} - {} - {} - {} - {} - {}'.format(show_id,season,episode,message,warning,error))

		# This is used to return a show's page based on imdb_id
		if search_id:
			show_id = Show.get_show_by_imdb_id(search_id).show_id
			message = None
			warning = None
			error = None
			logger.info('IMDB ID: {}'.format(search_id))
			logger.info('Got ID: {}'.format(show_id))

			return redirect('showView',show_id=show_id)

		# Look for an episode's page
		if episode:
			context = self.get_episode_page(request,show_id=show_id,season=season,episode=episode,message=message,warning=warning,error=error)

		# Look for a season's page
		elif season:
			context = self.get_season_page(request,show_id=show_id,season=season,message=message,warning=warning,error=error)

		# Look for a show's page
		elif show_id:
			context = self.get_show_page(request,show_id=show_id,message=message,warning=warning,error=error)

		# Look for a search result page
		elif search_term:
			context = self.get_imdb_search(request,search_term=search_term,message=message,warning=warning,error=error)

		# Look for a show by show name
		else:
			logger.info('REQUEST---{}'.format(request.path_info))
			if (request.path_info == '/tv/'):
				context = self.get_show_listing(request,message=message,warning=warning,error=error)
			else:
				try:
					context = self.get_search_page(request,message,warning,error)
				except InvalidShowId as i:
					logger.info('\tshow_id not found:{}'.format(show_id))
					context = self.get_search_page()

		# Render and return the response
		template = loader.get_template('query.html')
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
			#querytype = form.cleaned_data['querytype']
			queryvalue = form.cleaned_data['queryvalue']
			logger.info('\tform_validated: {}'.format(queryvalue))

			#ret = None
			#if querytype == 'search':
			ret = self.get(request,search_term=queryvalue)

			# Here we handle searches for a season number
			#elif querytype == 'season':
			#	ret = redirect('seasonView',show_id=show_id,season=queryvalue)

			# Here we handle searches for an episode number
			#elif querytype == 'episode':
			#	ret = redirect('episodeView',show_id=show_id, season=season,episode=queryvalue)

			# If we don't find a show, return the search page
			#else:
				#ret = APIView.get('shows',request=request,message='No results for: {}: {}'.format(querytype, queryvalue))
		else:
			# Just log and return None if the form is invalid
			logger.info('\tFORM INVALID')
			logger.info('\t{}'.format(form.errors))

		return ret

class InvalidInput(Exception):
	def __init__(self,message=None,field=None,value=None):
		super().__init__(message)
		self.field = field
		self.value = value
		self.message = message

	def __str__(self):
		return self.message

class InvalidEpisode(InvalidInput):
	def __init__(self,message=None,value=None):
		super().__init__(field='episode',value=value,message=message)

class InvalidSeason(InvalidInput):
	def __init__(self,message=None,value=None):
		super().__init__(field='season',value=value,message=message)

class InvalidShowId(InvalidInput):
	def __init__(self,message=None,value=None):
		super().__init__(field='show_id',value=value,message=message)
