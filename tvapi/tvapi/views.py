from django.http import HttpResponse
from django.views import View
from django.template import loader
from django.shortcuts import redirect
from .forms import BaseForm
from .apiclient import APIClient
import logging

logger = logging.getLogger('apilog')

REDACTED = ['Hamilton','hamilton']

class APIView(View):

	client = APIClient

	def match_found(list_data):
		match = False
		
		logger.info('MATCHED DATA: {}'.format(list_data))

		for char_pair in list_data:
			for k,v in char_pair.items():
				for r in REDACTED:
					if k.find(r) >= 0:
						match = True
					if v.find(r) >= 0:
						match = True

		return match

	def get(self, request,show_id=None,season=None,episode=None,show_name=None):
		logger.info('GET - {} - {} - {}'.format(show_id, season, episode))
		context = {'form': BaseForm}

		if episode:
			template = loader.get_template('query.html')

			cast = self.__class__.client.get_episode_cast(show_id=show_id,season=season,episode=episode)
			logger.info('episode-context: {}'.format(cast))

			match = APIView.match_found(cast)
			context.update({'match':match})
			
						

		
		elif season:
			template = loader.get_template('query.html')
			context.update(self.__class__.client.get_episodes(show_id=show_id,season=season))
			context['season'] = season
			#context['show_name'] = APIView.show_name

		elif show_id: 
			context.update({
				'show_name': self.__class__.client.get_show_name(show_id),
				'seasons': str(self.__class__.client.find_seasons(show_id)),
			})
			logger.info('Exception: {}'.format(e))
			self.__class__.client.get_show_imdb_id(show_id)


		else:
			template = loader.get_template('find_show.html')


		return HttpResponse(template.render(context,request))


	def post(self,request,show_id=None,season=None,episode=None):
		logger.info('POST - {}'.format(request))
		template = loader.get_template('query.html')
		form = BaseForm(request.POST)

		if form.is_valid():	
			querytype = form.cleaned_data['querytype']
			queryvalue = form.cleaned_data['queryvalue']

			ret = None
			if querytype == 'find_show':
				show_id = self.__class__.client.find_show(queryvalue)
				ret = redirect('showView', show_id=show_id)

			elif querytype == 'season':
				ret = redirect('seasonView', show_id=show_id,season=queryvalue)

			elif querytype == 'episode':
				ret = redirect('episodeView', show_id=show_id, season=season,episode=queryvalue)

		return ret

