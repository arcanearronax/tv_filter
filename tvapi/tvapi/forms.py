from django import forms

class BaseForm(forms.Form):
	querytype = forms.CharField(max_length=50)
	queryvalue = forms.CharField(max_length=50)
