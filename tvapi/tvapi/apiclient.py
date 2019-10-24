import requests
import json
import urllib.parse
import logging
from bs4 import BeautifulSoup
import re
from structures import *

logger = logging.getLogger('apilog')

tmdb_uri = 'https://api.themoviedb.org/3/'
api_key = 'c5b9f96015c7b3e771a36a2b43159f6d'
language = 'en-US'

class APIClient():
	# Shared Values
	shows = Season()

	# Used to encode url queries
	def url_encode(value):
		return urllib.parse.quote(value)

	@classmethod
	def get_show_name(cls,show_id):
		try:
			show_name = cls.shows['{}'.format(show_id)]
		except KeyError:
			url = '{}tv/{}?api_key={}&language={}'.format(tmdb_uri,show_id,api_key,language)
			req = requests.get(url)
			json_data = json.loads(req.text)
			show_name = json_data['name']
			cls.show_names['{}'.format(show_id)] = show_name

		return show_name

	@classmethod
	def find_show(cls,value):
		logger.info('find_show: {}'.format(value))
		url = '{}search/tv?api_key={}&language={}&query={}'.format(tmdb_uri, \
                api_key, language, APIClient.url_encode(value))
		req = requests.get(url)
		json_data = json.loads(req.text)
		tmdb_name = json_data['results'][0]['original_name']
		tmdb_id = json_data['results'][0]['id']
		#cls.show_names['{}'.format(tmdb_id)] = tmdb_name
		cls.shows.set(tmdb_id,tmdb_name)
		logger.info('tvmb_id: {}'.format(show_id))
		return show_id

	@classmethod
	def find_seasons(cls,show_id):
		logger.info('find_seasons: {}'.format(show_id))
		url = '{}tv/{}?api_key={}&language={}'.format(tmdb_uri, show_id, api_key, language)
		req = requests.get(url)
		json_data = json.loads(req.text)
		season = Season()
		season_cnt = int(json_data['number_of_seasons'])

		for i in range(1,season_cnt+1):
			cls.shows.add_season(show_id,i,season_cnt)

		return season_cnt

	@classmethod
	def get_episodes(cls,show_id,season):
		logger.info('get_episodes: {} - {}'.format(show_id,season))
		url = '{}tv/{}/season/{}?api_key={}&language={}'.format(tmdb_uri, show_id, season, api_key, language)
		req = requests.get(url)
		json_data = json.loads(req.text)
		episodes = json_data['episodes']

		for e in episodes:
			ep_num = e['episode_number']
			tmdb_id = e['id']
			tmdb_name = e['name']
			episode = Episode()
			episode.set(ep_num,tmdb_id=tmbd_id,tmdb_name=tmdb_name)
			cls.shows.set_episode(show_id,season,ep_num,episode)

		return len(episodes)

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

			json_data = json.loads(req.text)
			ret = json_data['Search'][0]['imdbID']
			cls.shows.set(show_id,imdb_id=ret)

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


	@classmethod
	def get_episode_cast(cls,show_id,season,ep_id):
		logger.info('get_episode_cast: {} - {} - {}'.format(show_id,season,episode))
		str_show_id = str(show_id)
		str_season = str(season)
		str_ep_id = str(ep_id)

		show_imdb_id = cls.get_show_imdb_id(str_show_id)
		logger.info('found_show_imdb_id: {}'.format(show_imdb_id))

		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(show_imdb_id,str_season)
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

		clear_div = ep_content.find('div',{'itemtype':'http://schema.org/TVSeason'})
		logger.info('8- {}'.format(clear_div.__class__))

		ep_list_div = clear_div.find('div', {'class':'list detail eplist'})
		logger.info('9- {}'.format(ep_list_div.__class__))

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
