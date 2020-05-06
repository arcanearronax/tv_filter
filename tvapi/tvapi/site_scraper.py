'''
This is a custom built web scraper/api client which communicates with IMDB and
TMDB in order to gather media data.

This is being modified to use threaded logic to pull data.
'''
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

tmdb_uri = 'https://api.themoviedb.org/3/'
api_key = 'c5b9f96015c7b3e771a36a2b43159f6d'
language = 'en-US'

# Used to encode url queries
def url_encode(value):
	return urllib.parse.quote(str(value))

logger = logging.getLogger('apilog')

class SiteScraper():

	@classmethod
	def get_imdb_title_search(cls,show_search):
		'''
		This is used to request the show search page from IMDB website for a
		given search. This will parse through the returned page and return an
		array containing dictionaries with information about the matches found.

		NOTE:
		It's possible that multiple results have identical names. The names
		should not be relied on to be unique.
		'''
		# Build the URL and get the IMDB page.
		url = 'https://www.imdb.com/find?q={}&s=tt'.format(url_encode(show_search))
		page = requests.get(url)

		# Get the table with the IMDB title data
		soup = BeautifulSoup(page.content,'html.parser')
		search_rows = soup.find_all('td', {'class':'result_text'})
		logger.info('Got search rows: {}'.format(len(search_rows)))
		logger.info('URL --- {}'.format(url))

		# Iterate over the rows with title information and build the array
		search_results = []
		for row in search_rows:
			result_a = row.a
			result_name = result_a.text

			result_info = {}
			result_info['imdb_id'] = re.search('tt[\d]{4,8}', result_a['href']).group(0)
			result_info['imdb_name'] = result_a.text
			#logger.info('FOUD: {}'.format(result_info))
			try:
				result_info['year'] = int(re.search('\([\d]{4}\)', row.text).group(0) \
				.replace('(','').replace(')','')) # Leaving this set to a default for now
			except TypeError as t: # If we fail to find a regex match
				result_info['year'] = None
			except AttributeError as a: # Hot fix time
				result_info['year'] = None
			except Exception as e:
				logger.info('EXCEPTION: {}'.format(e))
				result_info['year'] = None

			search_results.append(result_info)

		logger.info('Returning rows: {}'.format(len(search_results)))
		logger.info('RESULTS: {}'.format(search_results[:10]))
		return search_results[:10]

	@classmethod
	def get_show_imdb_info(cls, imdb_id):
		'''
		This returns a dictionary with info about the show from the show's IMDB
		page.
		'''
		url = 'https://www.imdb.com/title/{}'.format(url_encode(imdb_id))
		page = requests.get(url)

		# Get the table with the IMDB title data
		soup = BeautifulSoup(page.content,'html.parser')
		imdb_name = soup.find_all('div', {'class':'title_wrapper'})[0].h1.text
		logger.info('APIService.get_show_imdb_info: found - {}'.format(imdb_name))

		# Get season navbar from the page
		season_nav = soup.find('div', {'class': 'seasons-and-year-nav'})
		logger.info('GOT SEASON NAV: {}'.format(season_nav))
		link_list = season_nav.find_all('a')

		# Find the greatest season number
		max_season = 0
		for link in link_list:
			logger.info('LINK - {}'.format(link))
			link_value = link.text.replace(' ','')
			logger.info('LINK-VALUE - {}'.format(link_value))
			if (link.text.isdigit()):
				link_int = int(link.text)
				if (link_int < 1000):
					if (link_int > max_season):
						max_season = link_int

		# Find the year the show started airing
		year_title = soup.find_all('a', {'title': 'See more release dates'})[0]
		year = int(re.search('[\d]{4}', year_title.text).group(0))

		return {
			'imdb_id': imdb_id,
			'imdb_name': imdb_name,
			'seasons': max_season,
			'year': year,
		}



	@classmethod
	def get_imdb_seasons(cls, imdb_id):
		'''
		This is used to request the episodes page from IMDB website for a given
		IMDB ID. This will parse through the returned page and return an array
		containing dictionaries with season information for the show.
		'''

		# Build the URL and get the IMDB page.
		url = 'https://www.imdb.com/title/{}/episodes'.format(imdb_id)
		page = requests.get(url)

		# Get the menu with the season list
		soup = BeautifulSoup(page.content,'html.parser')
		season_menu = soup.find('select',{'id':'bySeason'})

		# Iterate over the values in the season menu
		show_seasons = []
		for season_option in season_menu.find_all('option'):
			season = {}
			season['imdb_id'] = imdb_id
			season['season_id'] = re.search('[\w]+',season_option.text).group(0)
			show_seasons.append(season)

		return show_seasons

	@classmethod
	def get_imdb_season(cls, show_id, season_num):
		'''
		This is used to request the season page from IMDB website for a given
		IMDB show id and season number. This will return a dictionary with
		information about the season.
		'''

		# Build the URL and get the IMDB page.
		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(show_id, season_num)
		page = requests.get(url)

		# Get the menu with the season list
		soup = BeautifulSoup(page.content,'html.parser')
		eps_div_odd = soup.find_all('div',{'class':'list_item odd'})
		eps_div_even = soup.find_all('div',{'class':'list_item even'})
		eps_div_full = eps_div_odd + eps_div_even

		# Iterate over the episode divs
		episodes = []
		max_ep_count = 0
		for ep in eps_div_full:
			# Get the image div
			image_div = ep.find('div',{'class':'image'})
			a_elem = image_div.find('a')

			a_div = a_elem.find('div')
			div_cont = a_div.find('div').text
			imdb_name = a_elem['title']

			ep_num = int(re.search('[\d]*$',div_cont).group(0))

			hover_div = a_elem.find('div',{'class':'hover-over-image'})
			ep_imdb_id = hover_div['data-const']

			logger.info('\tepisode: {} - {} - {}'.format(ep_num,ep_imdb_id,imdb_name))

			episodes.append({
				'ep_num': ep_num,
				'imdb_id': ep_imdb_id,
				'imdb_name': imdb_name,
			})

			if (ep_num > max_ep_count):
				max_ep_count = ep_num

		# Return the season dictionary
		return {
			'season_num': season_num,
			'ep_count': max_ep_count,
			'ep_list': episodes,
		}

	@classmethod
	def get_imdb_episode(cls,episode_id):
		'''
		This is used to request the episode page from IMDB website for a given
		IMDB show id, season number, and episode number. It returns a dictionary
		with information about the episode.
		'''
		logger.info('get_imdb_episode - {}'.format(episode_id))

		# Request the IMDB page
		url = 'https://www.imdb.com/title/{}'.format(episode_id)
		page = requests.get(url)

		# Get the menu with the season list
		soup = BeautifulSoup(page.content,'html.parser')
		heading_text = soup.find('div',{'class':'bp_heading'}).text

		# Parse out the season number, episode number, and episode_title
		season_num = re.findall('[\d]+', heading_text)[0]
		ep_num = re.findall('[\d]+', heading_text)[1]
		ep_name = soup.find('div',{'class':'title_wrapper'}).find('h1').text.strip(' ').strip('\xa0')
		logger.info('get_imdb_episode - found: {}'.format(ep_num))

		# Get the episode summary
		# kill...me...
		summary = soup.find('div',{'class':'summary_text'}).text\
		.strip('\n').strip(' ').strip('\n').strip('\xa0»')\
		.strip('See full summary').strip('\n')

		# Get the episode cast/crew
		crew_url = 'https://www.imdb.com/title/{}/fullcredits'.format(episode_id)
		crew_page = requests.get(crew_url)

		# Get an array with crew Tag elements to pull the actor and character from
		crew_soup = BeautifulSoup(crew_page.content,'html.parser')
		crew_row_odd = crew_soup.find_all('tr',{'class':'odd'})
		crew_row_even = crew_soup.find_all('tr',{'class':'even'})
		crew_row_full = crew_row_odd + crew_row_even
		logger.info('get_imdb_episode - cast_members: {}'.format(len(crew_row_full)))

		# Append dictionaries with the actor and character to the crew array
		crew = []
		for row in crew_row_full:
			crew_image = row.find('td',{'class':'primary_photo'})
			crew_name = crew_image.find('a').find('img')['alt']
			crew_character = row.find('td',{'class':'character'}).text.strip('\n')

			crew.append({
				'actor': crew_name,
				'character': crew_character,
			})

		# Return the episode dictionary
		return {
			'season_num': season_num,
			'ep_num': ep_num,
			'ep_name': ep_name,
			'summary': summary,
			'crew': crew,
		}

	@classmethod
	def get_imdb_episodes_single_thread(cls,show_id,season_num,episodes):
		'''
		This is used for performance comparisons against threaded methods.
		'''
		logger.info('get_imdb_episodes_single_thread - {} - {} - {}'.format(show_id, season, episodes))

		season = cls.get_imdb_season(show_id,season_num)
		ep_ids = [x['imdb_id'] for x in season['ep_list']]

		episodes = []
		for ep_id in ep_ids:
			episodes.append(cls.get_imdb_episode(ep_id))

		return episodes

	@classmethod
	def get_imdb_episodes(cls,show_id,season_num,episodes):
		'''
		This requires a show's IMDB ID, a valid season number be passed. If an
		array of numbers is passed as episodes, only those will be included in
		the response. This uses threaded logic to retreive and process each
		individual episode's IMDB page. A dictionary with information about
		the season is returned.
		'''
		logger.info('get_imdb_episodes - {} - {} - {}'.format(show_id, season, episodes))

		# Get the relevant episode ids
		season = cls.get_imdb_season(show_id,season_num)
		ep_ids = [x['imdb_id'] for x in season['ep_list']]

		# Create our array of episodes
		episodes = []
		with ThreadPoolExecutor(max_workers=10) as executor:

			# Build the threaded commands
			future_to_result = {executor.submit(cls.get_imdb_episode, ep_id): ep_id for ep_id in ep_ids}

			for future in as_completed(future_to_result):
				result = future_to_result[future]
				try:
					data = future.result()
				except Exception as e:
					logger.info(e)
				else:
					episodes.append(data)

		return episodes

	@classmethod
	def get_show_tmdb_info(cls,show_search):
		'''
		This is used to initiate a call to the TMDB API which searches for media
		which include a given search name and then initiates a second call to
		the TMDB API to pull data for the closest name matchself.
		This will return a dictionary with information about the show.
		'''
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
		'''
		This is used to initiate a call to the TMDB API which returns a list of
		episodes for a season of a given TMDB show ID. This will return an
		array which contains dictionaries with episode data.
		'''
		logger.info('APIService.get_episodes: {} - {}'.format(tmdb_id,season))

		url = '{}tv/{}/season/{}?api_key={}&language={}'.format(tmdb_uri, tmdb_id, season, api_key, language)
		logger.info('\turl: {}'.format(url))

		req = requests.get(url)
		json_data = json.loads(req.text)
		logger.info('\tjson_data len: {}'.format(len(json_data)))
		logger.info('\tjson_data len: {}'.format(json_data))

		try:
			episodes_arr = json_data['episodes']
			logger.info('\tepisodes: {}'.format(len(episodes_arr)))
		except Exception as e:
			logger.info('Encountered exception: {}'.format(e))
			raise ResourceNotFound('Failed to find page: {}'.format(json_data))


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

	@classmethod
	def get_episodes_imdb_info(cls,imdb_id,season):
		'''
		This requests the season page from IMDB's website for a given show and
		season then returns an array with dictionaries containing IMDB info for
		the episodes.
		'''
		logger.info('APIService.get_episodes_imdb_info: {} - {}'.format(imdb_id,season))

		url = 'https://www.imdb.com/title/{}/episodes?season={}'.format(imdb_id,season)
		logger.info('\turl: {}'.format(url))

		page = requests.get(url)

		if (page.status_code != 200):
			raise InvalidPage('Failed to retrieve page.',statuscode=page.status_code)

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
		'''
		This requests a given episode's cast page from the IMDB website. It
		returns an array containing dictonaries with an actor's and character's
		name.
		'''
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

	def __init__(self,text):
		logger.info('{}: {}'.format(self.__class__.__name__, text))
		#logger.info('{}: {}'.format(self.__class__.__name__,' - '.join(args)))
		super().__init__(text)
		self.text = text

class ResourceNotFound(APIException):
	"""Use this is we fail to find a resource we're looking for"""
	def __init__(self,text,resource=None):
		super().__init__(text)
		self.resource = resource
		logger.info('\tresource: {}'.format(self.resource))

class ElementNotFound(APIException):
	"""Use this is we get a page successfully, but we're missing something."""
	def __init__(self,text,element=None):
		super().__init__(text)
		self.element = element
		logger.info('\telement: {}'.format(self.element))

class InvalidPage(APIException):
	"""Use this is we have a failure retrieving source pages"""
	def __init__(self,text,statuscode=None):
		super().__init__(text)
		self.statuscode = statuscode
		logger.info('\tstatuscode: {}'.format(self.statuscode))
	pass
