import requests
import json
import urllib.parse
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger('apilog')

base_uri = 'https://api.themoviedb.org/3/'
api_key = 'c5b9f96015c7b3e771a36a2b43159f6d'
language = 'en-US'

class APIClient():

	show_names = {}

	show_imdb_ids = {}

	ep_imdb_ids = {}

	# Used to encode url queries
	def url_encode(value):
		return urllib.parse.quote(value)

	@classmethod
	def get_show_name(cls,show_id):
		try:
			show_name = cls.show_names['{}'.format(show_id)]
		except KeyError:
			url = '{}tv/{}?api_key={}&language={}'.format(base_uri, \
				show_id,api_key, language)
			req = requests.get(url)
			json_data = json.loads(req.text)
			show_name = json_data['name']
			cls.show_names['{}'.format(show_id)] = show_name
		
		return show_name

	@classmethod
	def find_show(cls,value):
		logger.info('find_show: {}'.format(value))
		
		url = '{}search/tv?api_key={}&language={}&query={}'.format(base_uri, \
                api_key, language, APIClient.url_encode(value))
		req = requests.get(url)
		json_data = json.loads(req.text)
		show_name = json_data['results'][0]['original_name']
		show_id = json_data['results'][0]['id']

		cls.show_names['{}'.format(show_id)] = show_name
		
		logger.info('tvmb_id: {}'.format(show_id))
		return show_id

	@classmethod
	def find_show_by_id(cls,show_id):
		logger.info('find_show_by_id: {}'.format(show_id))
			
		return {
			'show_name': cls.get_show_name(show_id)
		}

	@classmethod
	def find_seasons(cls,show_id):
		logger.info('find_seasons: {}'.format(show_id))

		url = '{}tv/{}?api_key={}&language={}'.format(base_uri, \
            show_id, api_key, language)

		req = requests.get(url)
		
		json_data = json.loads(req.text)

		seasons = json_data['number_of_seasons']

		return {
			'seasons': seasons,
			'show_name': cls.get_show_name(show_id),
			}

	@classmethod
	def get_episodes(cls,show_id,season):
		logger.info('get_episodes: {} - {}'.format(show_id,season))

		url = '{}tv/{}/season/{}?api_key={}&language={}'.format(base_uri, \
			show_id, season, api_key, language)

		req = requests.get(url)

		json_data = json.loads(req.text)

		episodes = len(json_data['episodes'])

		context = {'episodes': episodes}

		return {
			'episodes': episodes,
			'show_name': cls.get_show_name(show_id),
		}

	@classmethod
	def get_show_imdb_id(cls, show_id):
		logger.info('get_show_imdb_id: {}'.format(show_id))

		ret = None
		try:
			ret = cls.show_imdb_ids['{}'.format(show_id)]
		except KeyError:
			url = '{}'.format('https://movie-database-imdb-alternative.p.rapidapi.com/')

			headers = {
				'x-rapid-host': 'movie-database-imdb-alternative.p.rapidapi.com',
				'x-rapidapi-key': '7f282ba72amsh62fa1b3b0be127bp1fce1fjsn38c68fb682ad',
			}

			parameters = {
				'page': '1',
				'r': 'json',
				's': cls.get_show_name(show_id),
		}

			req = requests.get(url,headers=headers,params=parameters)
			#logger.info('req - {}'.format(req.text))
			json_data = json.loads(req.text)
			#logger.info('json - {}'.format(json_data))
	
			ret = json_data['Search'][0]['imdbID']
			#logger.info('ret - '.format(ret))

			cls.show_imdb_ids['{}'.format(show_id)] = ret 
			
		return ret

	@classmethod
	def get_show_imdb_season_list(cls, show_imdb_id, season):
		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(show_imdb_id,season)
		soup = BeautifulSoup(url)

		episode_div = soup.findAll('div', {'class': 'list_detail_eplist'})

		logger.info('episode_div - {}'.format(episode_div))

		

	@classmethod
	def get_episode_cast(cls,show_id,season,episode):
		logger.info('get_episode_cast: {} - {} - {}'.format(show_id,season,episode))

		try:
			cls.ep_imdb_ids[str(show_id)]
		except KeyError:
			cls.ep_imdb_ids.update({str(show_id):{str(season):{}}})
		else:
			try:
				cls.ep_imdb_ids[str(show_id)][str(season)]
			except KeyError:
				cls.ep_imdb_ids[str(show_id)][str(season)] = {}
			
		
		show_imdb_id = cls.get_show_imdb_id(show_id)
		logger.info('found_show_imdb_id: {}'.format(show_imdb_id))

		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(show_imdb_id,season)
		logger.info('SEASON_URL: {}'.format(url))

		page = requests.get(url)
		logger.info('STATUS: {})'.format(page.status_code))

		assert page.status_code == 200, 'Failed to retrieve page'

		soup = BeautifulSoup(page.content, 'html.parser')
		#logger.info('bs - {}'.format(soup))

		page_body = soup.find('body')
		logger.info('1- {}'.format(page_body.__class__))

		root_div = page_body.find('div', {'id': 'root'})
		logger.info('2- {}'.format(root_div.__class__))

		page_content = root_div.find('div',{'id':'pagecontent'})
		logger.info('3- {}'.format(page_content.__class__))

		content_2_wide = page_content.find('div', {'id': 'content-2-wide'})
		logger.info('4- {}'.format(content_2_wide.__class__))

		main_div = content_2_wide.find('div',{'id':'main'})
		logger.info('5- {}'.format(main_div.__class__))

		art_list = main_div.find('div',{'class':'article listo list'})
		logger.info('6- {}'.format(art_list.__class__))

		ep_content = art_list.find('div',{'id':'episodes_content'})
		logger.info('7- {}'.format(ep_content.__class__))
		#logger.info('7- {}'.format(str(ep_content)[:2000]))

		clear_div = ep_content.find('div',{'itemtype':'http://schema.org/TVSeason'})
		logger.info('8- {}'.format(clear_div.__class__))
		#logger.info('8 - {}'.format(clear_div.text))

		ep_list_div = clear_div.find('div', {'class':'list detail eplist'})
		logger.info('9- {}'.format(ep_list_div.__class__))

		#logger.info('LISTING --- {}'.format(ep_list_div))

		#for ep in ep_list_div:
		#	logger.info('ep - {}'.format(ep[:50]))

		logger.info('TESTING')

		ep_list_odd = ep_list_div.find_all('div', {'class': 'list_item odd'})
		logger.info('10- {}'.format(ep_list_odd.__class__))

		ep_list_even = ep_list_div.find_all('div', {'class':'list_item even'})
		logger.info('11- {}'.format(ep_list_even.__class__))

		ep_list_full = ep_list_odd + ep_list_even

		# Get the episode_imdb_ids
		ep_imdb_ids = {'{}'.format(show_id): {'{}'.format(season):{}} }

		logger.info('IMDB - {}'.format(ep_imdb_ids))

		#logger.info('ep_list_count: {}'.format(len(ep_list_full)))

		for ep in ep_list_full:
			#logger.info('ep_list_full - {}'.format(ep.text[:500]))
			image_div = ep.find('div',{'class':'image'})
			a_elem = image_div.find('a')

			a_div = a_elem.find('div')
			div_cont = a_div.find('div').text

			ep_num = re.search('[\d]*$',div_cont).group(0)
			logger.info('ep_num: {}'.format(ep_num))

			hover_div = a_elem.find('div',{'class':'hover-over-image'})
			ep_imdb_id = hover_div['data-const']		
			logger.info('emp_imdb_id: {}'.format(ep_imdb_id))

			# Build the json for the series' season
			ep_imdb_ids[str(show_id)][str(season)][str(ep_num)] = str(ep_imdb_id)

		logger.info('ep_imdb_ids - {}'.format(ep_imdb_ids))
		
		cls.ep_imdb_ids[str(show_id)][str(season)] = ep_imdb_ids[str(show_id)][str(season)]
		logger.info('CLASS ------- {}'.format(cls.ep_imdb_ids))


		#
		# Now we get the specified episode's cast page
		#
		

		epid = cls.ep_imdb_ids[str(show_id)][str(season)][str(episode)]	
		url = 'https://www.imdb.com/title/{}/fullcredits'.format(epid)
		req = requests.get(url)
		soup = BeautifulSoup(req.content,'html.parser')
		cast_table = soup.find('table', {'class':'cast_list'})

		logger.info('Flag 1')

		cast_odd = cast_table.find_all('tr', {'class':'odd'})
		cast_even = cast_table.find_all('tr', {'class':'even'})

		logger.info('1={} 2={}'.format(len(cast_odd),len(cast_even)))

		cast_full = cast_odd + cast_even

		#logger.info('full={}'.format(len(cast_full)))

		episode_cast = []
		for cast in cast_full:
			logger.info('Loop start')
			cast_photo = cast.find('td',{'class':'primary_photo'})
			cast_name = cast_photo.find('img')['title'].strip('\n')
			#logger.info('Actor: {}'.format(cast_name))

			cast_char = cast.find('td', {'class': 'character'}).text.replace('\n','')
			#logger.info('Char: {}'.format(cast_char))
			
			episode_cast.append({str(cast_name):str(cast_char)})

		return episode_cast

