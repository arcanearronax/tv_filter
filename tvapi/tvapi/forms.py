from django import forms
import logging

logger = logging.getLogger('apilog')

class PostForm(forms.Form):

	choices = (
		('search', 'Search by Name'),
		#('season', 'Season'),
		#('episode', 'Episode'),
	)

	#querytype = forms.ChoiceField(required=True,choices=choices,widget=forms.Select(attrs={'class':'w3-input w3-round w3-light-grey form-spacing'}))
	queryvalue = forms.CharField(max_length=50,widget=forms.TextInput(attrs={'class':'w3-input w3-round w3-light-grey form-spacing'}),label='Show Search')
	#testing = forms.TextInput()

class SearchForm(PostForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		#self.fields['querytype'].initial = self.choices[0]
		#self.fields['queryvalue'].class = "w3-input w3-round w3-grey"

class SeasonForm(PostForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		#self.fields['querytype'].initial = self.choices[1]

class EpisodeForm(PostForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		#self.fields['querytype'].initial = self.choices[2]
