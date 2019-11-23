import requests
import json
import urllib.parse
import logging
from bs4 import BeautifulSoup
import re
from .structures import *

logger = logging.getLogger('apilog')

tmdb_uri = 'https://api.themoviedb.org/3/'
api_key = 'c5b9f96015c7b3e771a36a2b43159f6d'
language = 'en-US'

class APIClient():
	# Shared Values
	shows = {}

	# Used to encode url queries
	def url_encode(value):
		return urllib.parse.quote(str(value))

	@classmethod
	def get_show_name(cls,tmdb_id):
		logger.info('get_show_name: {}'.format(tmdb_id))
		str_tmdb_id = str(tmdb_id)

		show_name = None
		try:
			show_name = cls.shows[str_tmdb_id].get('tmdb_name')
			logger.info('\tGot name: {}'.format(show_name))
		except KeyError:
			url = '{}tv/{}?api_key={}&language={}'.format(tmdb_uri,str_tmdb_id,api_key,language)
			req = requests.get(url)
			json_data = json.loads(req.text)
			tmdb_name = json_data['name']

			show = Show().set(tmdb_name=tmdb_name)
			cls.shows[str_tmdb_id] = show
			show_name = tmdb_name
			logger.info('\tcreated: {}'.format(show))

		return show_name

	@classmethod
	def find_show(cls,value):
		logger.info('find_show: {}'.format(value))
		url = '{}search/tv?api_key={}&language={}&query={}'.format(tmdb_uri, api_key, language, APIClient.url_encode(value))
		req = requests.get(url)

		json_data = json.loads(req.text)
		tmdb_name = json_data['results'][0]['original_name']
		tmdb_id = json_data['results'][0]['id']
		logger.info('tmdb_id: {}'.format(tmdb_id))

		show = Show().set(tmdb_id=tmdb_id,tmdb_name=tmdb_name)
		cls.shows[tmdb_id] = show

		return tmdb_id

	@classmethod
	def find_seasons(cls,tmdb_id):
		logger.info('find_seasons: {}'.format(tmdb_id))
		str_tmdb_id = str(tmdb_id)
		url = '{}tv/{}?api_key={}&language={}'.format(tmdb_uri,tmdb_id,api_key,language)
		req = requests.get(url)

		json_data = json.loads(req.text)
		season = Season()
		season_cnt = int(json_data['number_of_seasons'])

		for i in range(1,season_cnt+1):
			season = Season().set(season_num=str(i))
			logger.info('\tcreated: {}'.format(season))
			cls.shows[str_tmdb_id].set(season=season)

		logger.info('Found seasons: {}'.format(len(cls.shows[str_tmdb_id]['seasons'])))
		return season_cnt

	@classmethod
	def get_episodes(cls,show_tmdb_id,season_num):
		logger.info('get_episodes: {} - {}'.format(show_tmdb_id,season_num))
		str_season_num = str(season_num)
		url = '{}tv/{}/season/{}?api_key={}&language={}'.format(tmdb_uri, show_tmdb_id, str_season_num, api_key, language)
		req = requests.get(url)
		json_data = json.loads(req.text)
		episodes = json_data['episodes']

		logger.info('episode-count: {}'.format(str(len(episodes))))

		for ep in episodes:
			ep_num = ep['episode_number']
			tmdb_id = ep['id']
			tmdb_name = ep['name']
			episode = Episode()
			episode.set(ep_num=ep_num,tmdb_id=tmdb_id,tmdb_name=tmdb_name)
			logger.info('ep-created: {}'.format(episode))

			try:
				season = cls.shows[show_tmdb_id]['seasons'][str_season_num]
				season.set(episode=episode)
			except KeyError:
				cls.shows[show_tmdb_id]['seasons'][str_season_num] = Season().set(episode=episode)

		logger.info('Ep Count: {}'.format(len(cls.shows[show_tmdb_id]['seasons'][str_season_num]['episodes'])))
		return cls.shows[show_tmdb_id]['seasons'][str_season_num]['episodes']

	@classmethod
	def get_episode_count(cls,show_tmdb_id,season_num):
		logger.info('get_episode_count: {} - {}'.format(show_tmdb_id,season_num))
		str_season_num = str(season_num)
		ret = None
		try:
			ret = cls.shows[show_tmdb_id]['seasons'][str_season_num]['episodes']
			logger.info('Found:')
		except KeyError:
			ret = cls.get_episodes(show_tmdb_id,str_season_num)
			logger.info('Calculated')

		logger.info('Found episodes: {}'.format(len(cls.shows[show_tmdb_id]['seasons'][str_season_num])))
		return len(ret)

	@classmethod
	def get_show_imdb_id(cls,tmdb_id):
		logger.info('get_show_imdb_id: {}'.format(tmdb_id))

		str_tmdb_id = str(tmdb_id)
		ret = None
		try:
			ret = cls.shows.get(str_tmdb_id).get('imdb_id')
			logger.info('\tfound: {}'.format(ret))
		except KeyError:

			url = '{}'.format('https://movie-database-imdb-alternative.p.rapidapi.com/')
			headers = {
				'x-rapid-host': 'movie-database-imdb-alternative.p.rapidapi.com',
				'x-rapidapi-key': '7f282ba72amsh62fa1b3b0be127bp1fce1fjsn38c68fb682ad',
			}
			parameters = {
				'page': '1',
				'r': 'json',
				's': cls.get_show_name(tmdb_id),
			}
			req = requests.get(url,headers=headers,params=parameters)

			json_data = json.loads(req.text)
			ret = json_data['Search'][0]['imdbID']
			cls.shows[tmdb_id].set(imdb_id=ret)
			logger.info('\tcreated: {}'.format(ret))

		return ret

	@classmethod
	def get_season_imdb_info(cls,show_tmdb_id,season_num):
		logger.info('get_season_imdb_info: {}-{}'.format(show_tmdb_id, season_num))

		show_imdb_id = cls.shows.get(show_tmdb_id)['imdb_id']
		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(show_imdb_id,season)
		page = requests.get(url)
		assert page.status_code == 200, 'Failed to retrieve page'

		soup = BeautifulSoup(page.content, 'html.parser')
		eps_div_odd = soup.find('div',{'class':'list_item odd'})
		eps_div_even = soup.find('div',{'class':'list_item odd'})
		eps_div_full = ep_div_odd + ep_div_even

		for ep in ep_div_full:
			image_div = ep.find('div',{'class':'image'})
			a_elem = image_div.find('a')

			a_div = a_elem.find('div')
			div_cont = a_div.find('div').text

			ep_num = re.search('[\d]*$',div_cont).group(0)
			logger.info('ep_num: {}'.format(ep_num))

			hover_div = a_elem.find('div',{'class':'hover-over-image'})
			ep_imdb_id = hover_div['data-const']
			logger.info('emp_imdb_id: {}'.format(ep_imdb_id))

			cls.shows.set_episode(show_tmdb_id,season_num,ep_num,imdb_id,imdb_name)

		return self[str(show_tmdb_id)]['seasons'][str(season_num)]



	# This needs to be broken up into separate methodse
	@classmethod
	def get_episode_cast(cls,tmdb_show_id,season,ep_num):
		logger.info('get_episode_cast: {} - {} - {}'.format(tmdb_show_id,season,ep_num))
		str_tmdb_show_id = str(tmdb_show_id)
		str_season = str(season)
		str_ep_num = str(ep_num)

		show_imdb_id = cls.get_show_imdb_id(str_tmdb_show_id)
		logger.info('found_show_imdb_id: {}'.format(show_imdb_id))

		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(show_imdb_id,str_season)
		logger.info('SEASON_URL: {}'.format(url))

		page = requests.get(url)
		logger.info('STATUS: {})'.format(page.status_code))

		assert page.status_code == 200, 'Failed to retrieve page'

		soup = BeautifulSoup(page.content, 'html.parser')
		ep_list_odd = soup.find_all('div', {'class': 'list_item odd'})
		ep_list_even = soup.find_all('div', {'class':'list_item even'})
		ep_list_full = ep_list_odd + ep_list_even
		ep_imdb_ids = {'{}'.format(str_tmdb_show_id): {'{}'.format(season):{}} }

		for ep in ep_list_full:
			image_div = ep.find('div',{'class':'image'})
			a_elem = image_div.find('a')

			a_div = a_elem.find('div')
			div_cont = a_div.find('div').text

			imdb_ep_num = re.search('[\d]*$',div_cont).group(0)
			hover_div = a_elem.find('div',{'class':'hover-over-image'})
			str_ep_imdb_id = hover_div['data-const']

			episode = Episode().set(ep_num=imdb_ep_num,imdb_id=str_ep_imdb_id)
			cls.shows[tmdb_show_id]['seasons'][str_season].set(episode=episode)

		logger.info('ep_imdb_ids - {}'.format(ep_imdb_ids))

		#
		# Now we get the specified episode's cast page
		#

		url = 'https://www.imdb.com/title/{}/fullcredits'.format(cls.shows[tmdb_show_id]['seasons'][str_season]['episodes'][str_ep_num]['imdb_id'])
		logger.info('ep_url: {}'.format(url))
		req = requests.get(url)
		soup = BeautifulSoup(req.content,'html.parser')
		#logger.info('soup: {}'.format(soup))
		cast_table = soup.find('table', {'class':'cast_list'})

		#logger.info('cast_table: {}'.format(cast_table))

		cast_odd = cast_table.find_all('tr', {'class':'odd'})
		cast_even = cast_table.find_all('tr', {'class':'even'})
		logger.info('1={} 2={}'.format(len(cast_odd),len(cast_even)))
		cast_full = cast_odd + cast_even

		logger.info('EPISODESSSS: {}'.format(cls.shows[tmdb_show_id]['seasons'][str_season]['episodes']))

		episode_cast = []
		for cast in cast_full:
			logger.info('Loop start')
			cast_photo = cast.find('td',{'class':'primary_photo'})
			cast_name = cast_photo.find('img')['title'].strip('\n')
			cast_char = cast.find('td', {'class': 'character'}).text.replace('\n','')
			cls.shows[str_tmdb_show_id]['seasons'][str_season]['episodes'][str_ep_num]['cast'].set(cast_name,character=cast_char)

		logger.info('FINAL-EPISODES: {}'.format(cls.shows[str_tmdb_show_id]['seasons'][str_season]['episodes']))

		return cls.shows[str_tmdb_show_id]['seasons'][str_season]['episodes'][str_ep_num]['cast']
