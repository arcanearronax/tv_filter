from django import forms
import logging

logger = logging.getLogger('apilog')

class PostForm(forms.Form):

	choices = (
		('search', 'Search by Name'),
		('season', 'Season'),
		('episode', 'Episode'),
	)

	querytype = forms.ChoiceField(required=True,choices=choices)
	queryvalue = forms.CharField(max_length=50)

class SearchForm(PostForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['querytype'].initial = self.choices[0]

class SeasonForm(PostForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['querytype'].initial = self.choices[1]

class EpisodeForm(PostForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['querytype'].initial = self.choices[2]
