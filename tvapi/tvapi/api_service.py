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
	def get_show_name(cls,tmdb_id):
		logger.info('get_show_name: {}'.format(tmdb_id))
		str_tmdb_id = str(tmdb_id)

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
	def get_show_tmdb_info(cls,show_search):
		logger.info('get_show_tmdb_info: {}'.format(show_search))

		# First search for the show
		url = '{}search/tv?api_key={}&language={}&query={}'.format(tmdb_uri, api_key, language, url_encode(show_search))
		req = requests.get(url)

		json_data = json.loads(req.text)
		logger.info('json_data: {}'.format(json_data['results']))
		tmdb_name = json_data['results'][0]['original_name']
		tmdb_id = json_data['results'][0]['id']
		logger.info('tmdb_id: {}'.format(tmdb_id))

		# Then get the show's info
		url = '{}tv/{}?api_key={}&language={}'.format(tmdb_uri,tmdb_id,api_key,language)
		req = requests.get(url)

		json_data = json.loads(req.text)
		#logger.info('json_data2: {}')
		seasons = json_data['number_of_seasons']


		show = {
			'tmdb_id': tmdb_id,
			'tmdb_name': tmdb_name,
			'seasons': seasons,
		}

		return show

	@classmethod
	def get_episodes(cls,tmdb_id,season):
		logger.info('get_episodes: {} - {}'.format(tmdb_id,season))

		url = '{}tv/{}/season/{}?api_key={}&language={}'.format(tmdb_uri, tmdb_id, season, api_key, language)
		logger.info('url: {}'.format(url))
		req = requests.get(url)
		json_data = json.loads(req.text)
		#logger.info('json_data: {}'.format(json_data))
		episodes_arr = json_data['episodes']
		#logger.info('JSONNNN: {}'.format(episodes_arr))

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

		logger.info('RETURNING: {}'.format(episodes))
		return episodes

		logger.info('Ep Count: {}'.format(len(cls.shows[show_tmdb_id]['seasons'][str_season_num]['episodes'])))
		#return cls.shows[show_tmdb_id]['seasons'][str_season_num]['episodes']

	# Need to rebuild this to pull individal episode's imdb info
	@classmethod
	def get_show_imdb_info(cls,show_search):
		logger.info('get_episode_imdb_info: {}'.format(show_search))

		url = '{}'.format('https://movie-database-imdb-alternative.p.rapidapi.com/')
		headers = {
			'x-rapid-host': 'movie-database-imdb-alternative.p.rapidapi.com',
			'x-rapidapi-key': '7f282ba72amsh62fa1b3b0be127bp1fce1fjsn38c68fb682ad',
		}
		parameters = {
			'page': '1',
			'r': 'json',
			's': show_search,
		}

		req = requests.get(url,headers=headers,params=parameters)

		json_data = json.loads(req.text)
		imdb_id = json_data['Search'][0]['imdbID']
		imdb_name = json_data['Search'][0]['Title']

		episode_info = {
			'imdb_id': imdb_id,
			'imdb_name': imdb_name,
		}

		return episode_info

	@classmethod
	def get_episodes_imdb_info(cls,imdb_id,season):
		logger.info('get_episodes: {} - {}'.format(imdb_id,season))

		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(imdb_id,season)
		page = requests.get(url)
		logger.info('Page: {}'.format(url))
		assert page.status_code == 200, 'Failed to retrieve page'

		soup = BeautifulSoup(page.content, 'html.parser')
		eps_div_odd = soup.find_all('div',{'class':'list_item odd'})
		logger.info('eps_div_odd len: {}'.format(len(eps_div_odd)))
		eps_div_even = soup.find_all('div',{'class':'list_item even'})
		logger.info('eps_div_even len: {}'.format(len(eps_div_even)))
		eps_div_full = eps_div_odd + eps_div_even

		episodes = []

		# Cycle through the items
		for ep in eps_div_full:
			# Get the image div
			image_div = ep.find('div',{'class':'image'})
			a_elem = image_div.find('a')

			a_div = a_elem.find('div')
			div_cont = a_div.find('div').text
			#imdb_name = a_elem.find('title')
			imdb_name = a_elem['title']

			ep_num = re.search('[\d]*$',div_cont).group(0)
			#logger.info('ep_num: {}'.format(ep_num))

			hover_div = a_elem.find('div',{'class':'hover-over-image'})
			ep_imdb_id = hover_div['data-const']
			#logger.info('emp_imdb_id: {}'.format(ep_imdb_id))

			episode = {
				'ep_num': ep_num,
				'imdb_id': ep_imdb_id,
				'imdb_name': imdb_name,
			}

			logger.info('EP IMDB: {}'.format(episode))

			episodes.append(episode)

		logger.info('EPISODES---{}'.format(episodes))
		return episodes

	@classmethod
	def get_episode_cast(cls,ep_imdb_id):
		url = 'https://www.imdb.com/title/{}/fullcredits'.format(ep_imdb_id)
		logger.info('ep_url: {}'.format(url))
		req = requests.get(url)
		soup = BeautifulSoup(req.content,'html.parser')
		#logger.info('soup: {}'.format(soup))
		cast_table = soup.find('table', {'class':'cast_list'})

		cast_odd = cast_table.find_all('tr', {'class':'odd'})
		cast_even = cast_table.find_all('tr', {'class':'even'})
		logger.info('1={} 2={}'.format(len(cast_odd),len(cast_even)))
		cast_full = cast_odd + cast_even

		episode_cast = []
		for cast in cast_full:
			logger.info('Loop start')
			cast_photo = cast.find('td',{'class':'primary_photo'})
			cast_name = cast_photo.find('img')['title'].strip('\n')
			cast_char = cast.find('td', {'class': 'character'}).text.replace('\n','')
			#cls.shows[str_tmdb_show_id]['seasons'][str_season]['episodes'][str_ep_num]['cast'].set(cast_name,character=cast_char)
			episode_cast.append({
				'actor': cast_name,
				'character': cast_char,
			})

		return episode_cast
