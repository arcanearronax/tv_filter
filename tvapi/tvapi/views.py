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
		logger.info('APIView.get: {}'.format(show_id))

		context = {'form': BaseForm}
		template = loader.get_template('query.html')

		# If we fail, generic 404 page
		try:
			if episode:
				episode_id = Episode.get_episode_id(show_id=show_id,season=season,ep_num=episode)
				match = False
				for term in REDACTED:
					match = (Cast.get_match(episode_id,term) or match)

				context.update({
					'show_name': Show.get_show_name(show_id),
					'season': season,
					'episode': '{} - {}'.format(episode, Episode.get_name(show_id=show_id,season=season,ep_num=episode)),
					'match': match,
					'message': message,
				})

			elif season:
				#Episode.get_imdb_info(show_id,season)
				context.update({
					'show_name': Show.get_show_name(show_id),
					'season': season,
					'episodes': Episode.get_count(show_id=show_id,season=season),
					'message': message,
				})

			elif show_id:
				context.update({
					'show_name': Show.get_show_name(show_id),
					'seasons': Show.get_season_count(show_id),
					'message': message,
				})

			else:
				template = loader.get_template('find_show.html')
				context.update({
					'message': message,
				})
		except Exception as e:
			logger.info('APIView.get exception: {}'.format(e))
			raise Http404('Could Not Find Resource')
		else:
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
				try:
					show_id = Show.get_id_by_name(queryvalue)
				except ShowNotFound as s:
					logger.info('\tShowNotFound - {}'.format(s))
					request.method = 'GET'
					ret = redirect('shows',message='Failed to find: {}'.format(queryvalue))
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
