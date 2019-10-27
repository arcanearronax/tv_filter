import logging
#logger = logging.get#logger('apilog')
#
#shows = {
#    tmdb_id: {
#        'imdb_id': imdb_id,
#        'imdb_name': imdb_name,
#        'tmdb_name': tmdb_name,
#        'seasons': {
#            season: {
#                ep_id: {
#                    'tmdb_id': tmdb_id,
#                    'imdb_id': imdb_id,
#                    'tmdb_name': tmdb_name,
#                    'imdb_name': imdb_name,
#                    'cast': {
#                        actor: character,
#                        ...
#                    }
#                },
#                ...
#            },
#            ...
#        }
#    },
#    ...
#

class Cast(dict):
    def __init__(self):
        super().__init__()

    def get(self,actor=None):
        if actor:
            return self[str(actor)]
        return self

    def set(self,actor,character=None):
        str_actor = str(actor)
        str_char = str(character)
        self.update({str_actor: str_char})
        return self

class Episode(dict):

    def __init__(self):
        super().__init__()

    def get(self,tmdb_ep_id=None):
        if tmdb_ep_id:
            return self[str(tmdb_ep_id)]
        return self

    def set(self,ep_num,tmdb_id=None,imdb_id=None,tmdb_name=None,imdb_name=None,cast=None):
        str_ep_num = str(ep_num)
        str_tmdb_id = str(tmdb_id)
        str_imdb_id = str(imdb_id)
        str_tmdb_name = str(tmdb_name)
        str_imdb_name = str(imdb_name)

        self.update({
            'ep_num': str(ep_num),
            'tmdb_ep_id': str_tmdb_id,
            'imdb_id': str_imdb_id,
            'tmdb_name': str_tmdb_name,
            'imdb_name': str_imdb_name,
            'cast': cast,
            })

        return self


class Season(dict):

    def __init__(self):
        super().__init__()

    def get(self,ep_num=None):
        if ep_num:
            return self[str(ep_num)]
        return self

    def set(self,ep_num=None,episode=None,ep_cast=None):
        str_ep_num = str(ep_num)

        try:
            self[str_ep_num]
        except KeyError:
            #logger.info('Episode Not Found: {}'.format(str_tmdb_ep_id))
            self.update({str_ep_num: {}})

        if episode:
            self[str_ep_num] = episode
            if ep_cast:
                self[st_ep_num].set(cast=ep_cast)
        else:
            self[str_ep_num] = None

        return self


class Shows(dict):

    def __init__(self):
        super().__init__()

    def set_episode_cast(self,show_id,season_num,ep_num,cast):
        str_show_id = str(show_id)
        str_season = str(season_num)
        str_ep = str(ep_num)

        try:
            self[str_show_id]
        except KeyError:
            self.set(show_id)

        print('TEST - {}'.format(self))

        try:
            self[str_show_id]['seasons'][str_season]
        except KeyError:
            self.add_season(str_show_id,str_season,Season())

        self[str_show_id]['seasons'][str_season].set(str_ep,cast)

        return cast

    def set_episode(self,show_id,season_num,ep_num,episode=None,imdb_id=None,imdb_name=None):
        str_show_id = str(show_id)
        str_season = str(season_num)
        str_ep = str(ep_num)
        str_imdb_id = str(imdb_id)
        str_imdb_name = str(imdb_name)

        self[str_show_id]['seasons'][str_season][str_ep_num].set(ep_num,tmdb_id,tmdb_name,imdb_id,imdb_name)

        return {str_ep: episode}

    def add_season(self,show_id,season_num,season):
        str_show_id = str(show_id)
        str_season_num = str(season_num)

        try:
            self[show_id]['seasons'][season_num]
        except KeyError:
            #self[str_show_id]['seasons'] = None
            season = Season()
            self[show_id]['seasons'].update({str_season_num: season})

        self[show_id]['seasons'][season_num] = season

        return season

    def set(self,show_id,imdb_id=None,imdb_name=None,tmdb_name=None):
        str_show_id = str(show_id)
        str_imdb_id = str(imdb_id)
        str_imdb_name = str(imdb_name)
        str_tmdb_name = str(tmdb_name)

        try:
            self[str_show_id]
        except KeyError:
            #logger.info('No show found: {}'.format(str_show_id))
            self.update({str_show_id: {}})

        self[str_show_id].update({
            'tmdb_id': str_tmdb_id,
            'imdb_id': str_imdb_id,
            'imdb_name': str_imdb_name,
            'tmdb_name': str_tmdb_name,
            'seasons': {},
        })

    def get(self,show_id=None):
        if show_id:
            return self[str(show_id)]
        return self
