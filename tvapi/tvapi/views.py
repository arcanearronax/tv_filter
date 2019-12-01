from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views import View
from django.template import loader
from django.shortcuts import redirect
from .forms import BaseForm
from .models import *
import logging

logger = logging.getLogger('apilog')

REDACTED = ['Hamilton','hamilton']

class APIView(View):

	def get(self,request,show_id=None,season=None,episode=None,message=None):
		logger.info('APIView.get: {} - {} - {} - {}'.format(show_id,season,episode,message))

		context = {
			'form': BaseForm,
			'message': message,
		}
		template = loader.get_template('query.html')

		if message and not show_id:
			pass
		elif episode:
			logger.info('GETTING EPISODE')
			try:
				episode_id = Episode.get_episode_id(show_id=show_id,season=season,ep_num=episode)
			except IndexError as i:
				logger.info('TESTING: {}'.format(i))
				message = 'Episode does not exist: {}'.format(episode)
				return self.get(request,show_id,season=season,message=message)
			except Exception as e:
				logger.info('Exception-here: {}'.format(e))
				message = 'Episode does not exist: {}'.format(episode)
				return self.get(request,show_id,season=season,message=message)
			else:
				logger.info('Continuing to process')
				match = False
				for term in REDACTED:
					match = (Cast.get_match(episode_id,term) or match)

				context.update({
					'show_name': Show.get_show_name(show_id),
					'season': season,
					'episode': '{} - {}'.format(episode, Episode.get_name(show_id=show_id,season=season,ep_num=episode)),
					'match': match,
				})

		elif season:
			logger.info('GETTING SEASON')
			if show_id in ('None',''):
				logger.info('Show not provided')
				message = 'show_id not provided'
				return self.get(request,message=message)
			
			try:
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
					'season': season,
					'episodes': Episode.get_count(show_id=show_id,season=season),
				})

		elif show_id:
			context.update({
				'show_name': Show.get_show_name(show_id),
				'seasons': Show.get_season_count(show_id),
			})

		else:
			template = loader.get_template('find_show.html')

		return HttpResponse(template.render(context,request))


	def post(self,request,show_id=None,season=None,episode=None):
		logger.info('APIView.post - {} - {} - {}'.format(show_id,season,episode))
		template = loader.get_template('query.html')
		form = BaseForm(request.POST)

		if form.is_valid():
			logger.info('\tform_validated')
			querytype = form.cleaned_data['querytype']
			queryvalue = form.cleaned_data['queryvalue']
			logger.info('\tquerytype: {}'.format(querytype))
			logger.info('\tqueryvalue: {}'.format(queryvalue))

			ret = None
			if querytype == 'find_show':
				# Find search result or redirect with message
				try:
					show_id = Show.get_id_by_name(queryvalue)

				# If we don't find the show
				except ShowNotFound as s:
					logger.info('\tShowNotFound - {}'.format(s))
					message = 'Failed to find: {}'.format(queryvalue)
					ret = APIView.get(self,request,message=message)

				# If we don't get any search results
				except NoSearchResults as n:
					logger.info('\tNoSearchResults - {}'.format(n))
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
				ret = redirect('shows',request=request,message='No results for: {}: {}'.format(querytype, queryvalue))
		else:
			logger.info('\tFORM INVALID')

		return ret
