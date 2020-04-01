from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views import View
from django.template import loader
from django.shortcuts import redirect, reverse
from .forms import *
from .models import *
from .redactions import words
import logging
from .api_service import APIService
import time

logger = logging.getLogger('apilog')

class APIView(View):

	# Decorator to validate inputs
	def validate_inputs(func):
		def wrapper(*args,**kwargs):
			logger.info('validating inputs')

			logger.info('VALIDATE_ARGS: {}'.format(len(args)))

			show_id = args[2]
			season = args[3]
			episode = args[4]

			# Raise an error or passes
			def validate_show_id(show_id):
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
				try:
					int(season)
					return True
				except ValueError:
					raise InvalidSeason(value=season,message='Not an int - season')

				return False

			def validate_episode(episode):
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

	@validate_inputs
	def get_episode_page(self,request,show_id,season,episode,message=None,warning=None,error=None):
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
				'form': EpisodeForm,
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
				'form': EpisodeForm,
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
				'form': EpisodeForm,
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
					'season': season,
					'episode': '{} - {}'.format(episode, Episode.get_name(show_id=show_id,season=season,ep_num=episode)),
					'match': match,
					'page_h1': show_name,
				})
			except InvalidPage as i:
				show_name = Show.get_show_name(show_id)
				context.update({
					'show_name': show_name,
					'form': EpisodeForm,
					'season': season,
					'warning': i,
					'match': match,
					'page_h1': show_name,
				})

		return context

	@validate_inputs
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
				'show_name': show_name,
				'form': SeasonForm,
				'episode_count': Episode.get_count(show_id=show_id,season=season),
				'page_h1': show_name,
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
				'show_name': show_name,
				'form': EpisodeForm,
				'season': season,
				'episodes': episodes,
				'page_h1': show_name,
			}

		return context

	@validate_inputs
	def get_show_page(self,request,show_id,message=None,warning=None,error=None):
		logger.info('APIView.get_show_page: {} - {} - {} - {}'.format(show_id,message,warning,error))

		show_name = Show.get_show_name(show_id)
		context = {
			'message': message,
			'warning': warning,
			'error': error,
			'show_name': show_name,
			'form': SeasonForm,
			'seasons': Show.get_season_count(show_id),
			'page_h1': show_name,
		}

		return context

	def get_search_page(self,request,message=None,warning=None,error=None):
		logger.info('APIView.get_show: {} - {} - {}'.format(message,warning,error))
		context = {
			'message': message,
			'warning': warning,
			'error': error,
			'form': SearchForm,
			'page_h1': 'Search for a show'
		}

		return context



	@classmethod
	def test_view(cls, request):
		'''
		This is used solely as a shortcut for testing.
		'''
		logger.info('APIView.test_view: {}'.format(request))
		template = loader.get_template('test.html')

		service = APIService()

		single_start = time.time()
		episodes = service.get_imdb_episodes_single_thread('tt0413573',12,5)
		single_finish = time.time()

		multi_start = time.time()
		episodes = service.get_imdb_episodes('tt0413573',12,5)
		multi_finish = time.time()

		context = {
			#'episodes': service.get_imdb_episodes('tt0413573', 12, 2),
			'single_start': single_start,
			'single_finish': single_finish,
			'multi_start': multi_start,
			'multi_finish': multi_finish,
			'single_time': single_finish - single_start,
			'multi_time': multi_finish - multi_start,
		}

		return HttpResponse(template.render(context, request))




	def get(self,request,show_id=None,season=None,episode=None,message=None,warning=None,error=None):
		logger.info('APIView.get: {} - {} - {} - {} - {} - {}'.format(show_id,season,episode,message,warning,error))

		if episode: # Look for an episode
			context = self.get_episode_page(request,show_id,season,episode,message,warning,error)

		elif season: # Look for a season
			context = self.get_season_page(request,show_id,season,message,warning,error)

		elif show_id: # Look for a show by id
			context = self.get_show_page(request,show_id,message,warning,error)

		else: # Look for a show by show name
			try:
				context = self.get_search_page(request,message,warning,error)
			except InvalidShowId as i:
				logger.info('\tshow_id not found:{}'.format(show_id))
				context = self.get_search_page()

		template = loader.get_template('query.html')
		return HttpResponse(template.render(context,request))

	# This should only redirect or return a get call
	def post(self,request,show_id=None,season=None,episode=None):
		logger.info('APIView.post - {} - {} - {}'.format(show_id,season,episode))
		template = loader.get_template('query.html')
		form = PostForm(request.POST)

		if form.is_valid():

			querytype = form.cleaned_data['querytype']
			queryvalue = form.cleaned_data['queryvalue']
			logger.info('\tform_validated: {} - {}'.format(querytype,queryvalue))

			ret = None
			if querytype == 'search':

				# Find search result or redirect with message
				try:
					show_id = Show.get_id_by_name(queryvalue)

				except ResourceNotFound as s:
					warning = 'Failed to find: {}'.format(queryvalue)
					ret = APIView.get(self,request,warning=warning)

				except InvalidPage as n:
					message = 'No Results for {}'.format(queryvalue)
					ret = APIView.get(self,request,message=message)

				else:
					ret = redirect('showView',show_id=show_id)

			elif querytype == 'season':
				ret = redirect('seasonView',show_id=show_id,season=queryvalue)

			elif querytype == 'episode':
				ret = redirect('episodeView',show_id=show_id, season=season,episode=queryvalue)

			else:
				#request.method = 'GET'
				ret = APIView.get('shows',request=request,message='No results for: {}: {}'.format(querytype, queryvalue))
		else:
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
