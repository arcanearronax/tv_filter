from django.http import HttpResponse
from django.views import View
from django.template import loader
from django.shortcuts import redirect
from .forms import BaseForm
from .models import *
import logging

logger = logging.getLogger('apilog')

REDACTED = ['Hamilton','hamilton']

class APIView(View):

	def get(self,request,show_id=None,season=None,episode=None):
		logger.info('APIView.get: {}'.format(show_id))

		context = {'form': BaseForm}
		template = loader.get_template('query.html')

		if episode:
			logger.info('episode-context: {}'.format(show_id))
			episode_id = Episode.get_episode_id(show_id=show_id,season=season,ep_num=episode)
			match = False

			for term in REDACTED:
				logger.info('Looping')
				match = (Cast.get_match(episode_id,term) or match)

			context.update({
				'show_name': Show.get_show_name(show_id),
				'season': season,
				'episode': '{} - {}'.format(episode, Episode.get_name(show_id=show_id,season=season,ep_num=episode)),
				'match': match,
			})

		elif season:
			logger.info('GET_SEASON')
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
		logger.info('APIView.post - {}'.format(request))
		template = loader.get_template('query.html')
		form = BaseForm(request.POST)

		if form.is_valid():
			logger.info('form_validated')
			querytype = form.cleaned_data['querytype']
			queryvalue = form.cleaned_data['queryvalue']

			ret = None
			if querytype == 'find_show':
				show_id = Show.get_id_by_name(queryvalue)
				ret = redirect('showView',show_id=show_id)

			elif querytype == 'season':
				ret = redirect('seasonView',show_id=show_id,season=queryvalue)

			elif querytype == 'episode':
				ret = redirect('episodeView',show_id=show_id, season=season,episode=queryvalue)

		return ret
