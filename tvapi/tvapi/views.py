from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views import View
from django.template import loader
from django.shortcuts import redirect
from .forms import *
from .models import *
from .redactions import words
import logging

logger = logging.getLogger('apilog')

class APIView(View):

	def get(self,request,show_id=None,season=None,episode=None,message=None):
		logger.info('APIView.get: {} - {} - {} - {}'.format(show_id,season,episode,message))

		# Let's get our default variables
		context = {
			'message': message,
		}
		template = loader.get_template('query.html')

		if episode:
			logger.info('GETTING EPISODE')

			try: # Look for the episode
				# We should probably just grab the episode as a var
				episode_id = Episode.get_episode_id(show_id=show_id,season=season,ep_num=episode)

			except IndexError as i:
				logger.info('TESTING: {}'.format(i))
				message = 'Episode does not exist: {}'.format(episode)
				return self.get(request,show_id,season=season,message=message)

			except Exception as e:
				logger.info('Exception-here: {}'.format(e))
				message = 'Episode does not exist: {}'.format(episode)
				return self.get(request,show_id,season=season,message=message)

			else: # Found the episode, get the cast info
				logger.info('Continuing to process')
				match = False

				try: # Loop over the cast, looking for a match
					for term in words:
						match = (Cast.get_match(episode_id,term) or match)

				except CastException as c: # Oops
					context.update({
						'message': str(c),
					})

				context.update({
					'show_name': Show.get_show_name(show_id),
					'form': EpisodeForm,
					'season': season,
					'episode': '{} - {}'.format(episode, Episode.get_name(show_id=show_id,season=season,ep_num=episode)),
					'match': match,
				})

		elif season: # Look for a season
			logger.info('GETTING SEASON')

			if show_id in ('None',''): # Minimal show_id validation
				logger.info('Show not provided')
				message = 'show_id not provided'
				return self.get(request,message=message)

			try: # Get the episode count for the season
				episodes = Episode.get_count(show_id,season=season)
				logger.info('GOT EPISODES')
			except Exception:
				message = 'Season does not exist: {}'.format(season)
				logger.info('RETURNING SHOW')
				return self.get(request,show_id=show_id,message=message)
			else:
				logger.info('RETURNING SEASON')
				context.update({
					'show_name': Show.get_show_name(show_id),
					'form': EpisodeForm,
					'season': season,
					'episodes': Episode.get_count(show_id=show_id,season=season),
				})

		elif show_id: # Look for a show by id
			context.update({
				'show_name': Show.get_show_name(show_id),
				'form': SeasonForm,
				'seasons': Show.get_season_count(show_id),
			})

		else: # Look for a show by show name
			context.update({
				'form': SearchForm,
			})
			template = loader.get_template('find_show.html')

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
					message = 'Failed to find: {}'.format(queryvalue)
					ret = APIView.get(self,request,message=message)

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
