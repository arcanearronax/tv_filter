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

logger = logging.getLogger('structlog')

class Cast(dict):
    def __init__(self):
        super().__init__()

    def get(self,actor=None):
        if actor:
            try:
                return self[str(actor)]
            except KeyError:
                return None
        return self

    def set(self,actor,character=None):
        str_actor = str(actor)
        str_char = str(character)
        self.update({str_actor: str_char})
        return self

#
# tmdb_ep_num
# tmdb_id
# tmdb_name
# tmdb_ep_num
# imdb_id
# imdb_name
# cast
#
class Episode(dict):

    def __init__(self):
        super().__init__()
        self.set(cast=Cast())

    def get(self,*args):
        assert len(args) < 2, 'Only 1 arg permitted.'
        if args:
            return self[args[0]]
        return self

    def set(self,**kwargs):
        for k,v in kwargs.items():
            k = str(k)
            print('setting: {} - {}'.format(k,v))

            self.update({
                k: v,
            })

        return self

#
# season_num
# episodes
#
class Season(dict):

    def __init__(self):
        super().__init__()
        self.set(episodes={})

    def get(self,*args):
        assert len(args) < 2, 'Only 1 arg permitted.'
        if args:
            return self[args[0]]
        return self

    def set(self,**kwargs):
        for k,v in kwargs.items():
            k = str(k)

            if k == 'episode':
                ep_num = v.get('ep_num')

                if ep_num:
                    logger.info('ADDING EPISODE: {}'.format(ep_num))
                    self['episodes'].update({
                        str(ep_num): v,
                    })

            elif k == 'episodes':
                self.update({
                    'episodes': {},
                })

            else:
                self.update({
                    k: v,
                })
        logger.info('SETTING-1: {}'.format(self))
        return self


#
# tmdb_id
# tmdb_name
# imdb_id
# imdb_name
# seasons
#
class Show(dict):

    def __init__(self):
        super().__init__()
        self.set(seasons={})
        logger.info('set season: {}'.format(self['seasons'].__class__))

    def get(self,*args):
        assert len(args) < 2, 'Only 1 arg permitted.'
        if args:
            return self[args[0]]
        return self

    def set(self,**kwargs):
        logger.info('Setting val for: {}'.format(self))
        for k,v in kwargs.items():
            k = str(k)
            logger.info('SHOW-SET: {} - {}'.format(k,v))

            if k == 'season':
                #logger.info('\t\tSEASON_TYPE: {}'.format(self['seasons'].__class__))
                season_num = v.get('season_num')
                logger.info('season_num: {}'.format(season_num))

                self['seasons'].update({
                    str(season_num): v,
                })

            elif k == 'seasons':
                logger.info('\tcreating new season')
                self.update({
                    'seasons': {}
                })
            else:
                self.update({
                    k: v,
                })
        logger.info('SETTING-0: {}'.format(self))
        return self
