"""
    tvapi.forms
"""

import logging
from django import forms

logger = logging.getLogger("apilog")


class PostForm(forms.Form):
    """
    This is a base form used to provide
    """

    choices = (
        ("search", "Search by Name"),
    )

    queryvalue = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={"class": "w3-input w3-round w3-light-grey form-spacing"}
        ),
        label="Show Search",
    )


class SearchForm(PostForm):
    """
    This is a form used to search for TV shows.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['querytype'].initial = self.choices[0]
        # self.fields['queryvalue'].class = "w3-input w3-round w3-grey"


class SeasonForm(PostForm):
    """
    This is a form used to search for TV seasons.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['querytype'].initial = self.choices[1]


class EpisodeForm(PostForm):
    """
    This is a form used to search for TV episodes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['querytype'].initial = self.choices[2]
