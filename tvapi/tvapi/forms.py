from django import forms
import logging

logger = logging.getLogger('apilog')

class BaseForm(forms.Form):
	querytype = forms.CharField(max_length=10)
	queryvalue = forms.CharField(max_length=50)

class SearchForm(BaseForm):
	def __init__(self,*args,**kwargs):

		modifications = {
			'widget': 'forms.HiddenInput()',
			'required': 'False',
			'initial': 'find_show'
		}

		super().__init__(*args,**kwargs)
		for k,v in modifications.items():
			eval("self.fields['querytype'].{}={}".format(k,v))
		#self.fields['querytype'].widget=forms.HiddenInput()
		#self.fields['querytype'].required=False
		#self.fields['querytype'].initial='find_show'

class ShowForm(BaseForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		#self.fields['querytype'].widget=forms.HiddenInput()
		self.fields['querytype'].initial='show'

class SeasonForm(BaseForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		#self.fields['querytype'].widget=forms.HiddenInput()
		self.fields['querytype'].initial='season'

class EpisodeForm(BaseForm):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		#self.fields['querytype'].widget=forms.HiddenInput()
		self.fields['querytype'].initial='episode'
