import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
import re
import logging

tmdb_uri = 'https://api.themoviedb.org/3/'
api_key = 'c5b9f96015c7b3e771a36a2b43159f6d'
language = 'en-US'

# Used to encode url queries
def url_encode(value):
	return urllib.parse.quote(str(value))

logger = logging.getLogger('apilog')

class APIService():

	@classmethod
	def get_show_tmdb_info(cls,show_search):
		logger.info('APIService.get_show_tmdb_info: {}'.format(show_search))

		# First search for the show
		url = '{}search/tv?api_key={}&language={}&query={}'.format(tmdb_uri, api_key, language, url_encode(show_search))
		logger.info('\turl: {}'.format(url))

		try:
			req = requests.get(url)
			json_data = json.loads(req.text)
			logger.info('\tjson_data len: {}'.format(len(json_data['results'])))


			tmdb_name = json_data['results'][0]['original_name']
			tmdb_id = json_data['results'][0]['id']
		except Exception as e:
			logger.info('\texception: {}'.format(e))
			raise ResourceNotFound('show_search: {}'.format(show_search))
		logger.info('\ttmdb: {} - {}'.format(tmdb_id, tmdb_name))

		# Then get the show's info
		url = '{}tv/{}?api_key={}&language={}'.format(tmdb_uri,tmdb_id,api_key,language)
		logger.info('\turl: {}'.format(url))
		req = requests.get(url)

		json_data = json.loads(req.text)
		logger.info('\tjson_data len: {}'.format(len(json_data)))
		seasons = json_data['number_of_seasons']


		show = {
			'tmdb_id': tmdb_id,
			'tmdb_name': tmdb_name,
			'seasons': seasons,
		}

		return show

	@classmethod
	def get_episodes(cls,tmdb_id,season):
		logger.info('APIService.get_episodes: {} - {}'.format(tmdb_id,season))

		url = '{}tv/{}/season/{}?api_key={}&language={}'.format(tmdb_uri, tmdb_id, season, api_key, language)
		logger.info('\turl: {}'.format(url))

		req = requests.get(url)
		json_data = json.loads(req.text)
		logger.info('\tjson_data len: {}'.format(len(json_data)))

		episodes_arr = json_data['episodes']
		logger.info('\tepisodes: {}'.format(len(episodes_arr)))

		episodes = []
		for ep in episodes_arr:
			ep_num = ep['episode_number']
			tmdb_id = ep['id']
			tmdb_name = ep['name']

			episodes.append({
				'ep_num': ep_num,
				'tmdb_id': tmdb_id,
				'tmdb_name': tmdb_name,
			})

		logger.info('\treturning: {}'.format(len(episodes)))
		return episodes


	# Need to rebuild this to pull individal episode's imdb info
	@classmethod
	def get_show_imdb_info(cls,show_search):
		logger.info('APIService.get_episode_imdb_info: {}'.format(show_search))

		url = '{}'.format('https://movie-database-imdb-alternative.p.rapidapi.com/')
		logger.info('\turl: {}'.format(url))

		headers = {
			'x-rapid-host': 'movie-database-imdb-alternative.p.rapidapi.com',
			'x-rapidapi-key': '7f282ba72amsh62fa1b3b0be127bp1fce1fjsn38c68fb682ad',
		}
		parameters = {
			'page': '1',
			'r': 'json',
			's': show_search,
		}

		try:
			req = requests.get(url,headers=headers,params=parameters)

			json_data = json.loads(req.text)
			logger.info('\tjson_data len: {}'.format(len(json_data)))

			imdb_id = json_data['Search'][0]['imdbID']
			imdb_name = json_data['Search'][0]['Title']
			logger.info('\timdb: {} - {}'.format(imdb_id,imdb_name))
		except KeyError as s:
			raise ResourceNotFound('Failed to find: {}'.format(show_search))

		episode_info = {
			'imdb_id': imdb_id,
			'imdb_name': imdb_name,
		}

		return episode_info

	@classmethod
	def get_episodes_imdb_info(cls,imdb_id,season):
		logger.info('APIService.get_episodes_imdb_info: {} - {}'.format(imdb_id,season))

		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(imdb_id,season)
		logger.info('\turl: {}'.format(url))

		page = requests.get(url)

		if (page.status_code != 200):
			raise InvalidPage('Status code: {}'.format(page.status_code))

		soup = BeautifulSoup(page.content, 'html.parser')
		eps_div_odd = soup.find_all('div',{'class':'list_item odd'})
		eps_div_even = soup.find_all('div',{'class':'list_item even'})
		eps_div_full = eps_div_odd + eps_div_even
		logger.info('\teps_div_full: {}'.format(len(eps_div_full)))

		episodes = []

		# Cycle through the items
		for ep in eps_div_full:
			# Get the image div
			image_div = ep.find('div',{'class':'image'})
			a_elem = image_div.find('a')

			a_div = a_elem.find('div')
			div_cont = a_div.find('div').text
			imdb_name = a_elem['title']

			ep_num = re.search('[\d]*$',div_cont).group(0)

			hover_div = a_elem.find('div',{'class':'hover-over-image'})
			ep_imdb_id = hover_div['data-const']

			logger.info('\tepisode: {} - {} - {}'.format(ep_num,ep_imdb_id,imdb_name))

			episode = {
				'ep_num': ep_num,
				'imdb_id': ep_imdb_id,
				'imdb_name': imdb_name,
			}

			episodes.append(episode)

		logger.info('\treturning'.format(len(episodes)))
		return episodes

	@classmethod
	def get_episode_cast(cls,ep_imdb_id):
		logger.info('APIService.get_episode_cast: {}'.format(ep_imdb_id))

		url = 'https://www.imdb.com/title/{}/fullcredits'.format(ep_imdb_id)
		logger.info('\turl: {}'.format(url))

		req = requests.get(url)
		soup = BeautifulSoup(req.content,'html.parser')
		cast_table = soup.find('table', {'class':'cast_list'})

		try:
			cast_odd = cast_table.find_all('tr', {'class':'odd'})
			cast_even = cast_table.find_all('tr', {'class':'even'})
		except AttributeError as a:
			logger.info('\tAttributeError: {}'.format(a))
			raise ElementNotFound('Missing Cast Rows')
		else:
			cast_full = cast_odd + cast_even
			logger.info('\tcast_full len: {}'.format(len(cast_full)))

		episode_cast = []
		for cast in cast_full:
			cast_photo = cast.find('td',{'class':'primary_photo'})
			cast_name = cast_photo.find('img')['title'].strip('\n')
			cast_char = cast.find('td', {'class': 'character'}).text.replace('\n','')
			episode_cast.append({
				'actor': cast_name,
				'character': cast_char,
			})

		logger.info('\treturning: {}'.format(len(episode_cast)))
		return episode_cast

class APIException(Exception):
	"""Base class for API exceptions"""

	def __init__(self,*args,**kwargs):
		#logger.info('{}: {}'.format(self.__class__.__name__,' - '.join(args)))
		print('{}: {}'.format(self.__class__.__name__,' - '.join(args)))
		super().__init__(args,kwargs)

class ResourceNotFound(APIException):
	"""Use this is we fail to find a resource we're looking for"""
	pass

class ElementNotFound(APIException):
	"""Use this is we get a page successfully, but we're missing something."""
	pass

class InvalidPage(APIException):
	"""Use this is we have a failure retrieving source pages"""
	pass
