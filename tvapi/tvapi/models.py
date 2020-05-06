from django.db import models
from django.core.exceptions import ValidationError
from django.db import DataError
from .site_scraper import *
import logging

logger = logging.getLogger('modellog')
site_scraper = SiteScraper

class Show(models.Model):
    '''
    This model represents Show objects.
    If a given episode is not found, it will be searched for on IMDB.
    '''
    show_id = models.AutoField(primary_key=True)
    tmdb_id = models.IntegerField(null=True)
    tmdb_name = models.CharField(max_length=100,null=True)
    imdb_id = models.CharField(max_length=9,null=True)
    imdb_name = models.CharField(max_length=100,null=True)
    seasons = models.IntegerField(null=True)
    year = models.IntegerField(null=True)

    @classmethod
    def get_show_name(cls,show_id):
        '''
        This is responsible for finding a show's name based on the show_id.
        If a show_id is not found a ShowException will be raised.
        '''
        logger.info('Show.get_show_name: {}'.format(show_id))

        # Look for the IMDB name
        try:
            ret = cls.objects.get(show_id=show_id).imdb_name

        # If we don't find it, log the error and return None
        except cls.DoesNotExist as dne:
            logger.error('get_show_name error: {}'.format(dne.__class__))
            raise ShowException('No show found for ID: {}'.format(show_id))

        return ret

    @classmethod
    def get_season_count(cls,show_id=show_id):
        '''
        This is used to return the number of seasons for a given show_id.
        If a show_id is not found a ShowException will be raised.
        '''
        logger.info('Show.get_season_count: {}'.format(show_id))

        # Look for the show in the db
        try:
            ret = cls.objects.get(show_id=show_id).seasons

        # Log the error and return -1
        except Exception as e:
            logger.error('get_season_count error: {}'.format(e))
            ret = -1

        return ret

    @classmethod
    def get_show_by_imdb_id(cls, imdb_id_search):
        '''
        This returns a show based on its imdb_id.
        '''
        logger.info('Show.get_show_by_imdb_id: {}'.format(imdb_id_search))

        # Look for a show with a matching imdb_id
        try:
            ret = cls.objects.get(imdb_id=imdb_id_search)

        # If we don't find it, retrieve it from IMDB and create it
        except Exception as e:
            show_imdb_info = site_scraper.get_show_imdb_info(imdb_id_search)

            # NEED TO CONTINUE WORKING FROM HERE
            imdb_id = show_imdb_info['imdb_id']
            imdb_name = show_imdb_info['imdb_name']
            seasons = show_imdb_info['seasons']
            year = show_imdb_info['year']

            show = cls(imdb_id=imdb_id, imdb_name=imdb_name, seasons=seasons, year=year)
            show.save()
            ret = show

        return ret

    @classmethod
    def get_shows(cls,limit=0):
        '''
        This method is used to return a result set of shows. It can be limited
        if limit != 0.
        '''
        if (limit):
            ret = cls.objects.all()[0:limit]
        else:
            ret = cls.objects.all()

        return ret

class Episode(models.Model):
    '''
    This model represents Episode objects.
    If a given episode is not found, it will be searched for on IMDB.
    '''
    episode_id = models.AutoField(primary_key=True)
    ep_num = models.IntegerField(null=True)
    tmdb_id = models.IntegerField(null=True)
    tmdb_name = models.CharField(null=True,max_length=100)
    imdb_id = models.CharField(null=True,max_length=9)
    imdb_name = models.CharField(null=True,max_length=100)
    show = models.ForeignKey(Show,on_delete=models.CASCADE)
    season = models.IntegerField()

    site_scraper = SiteScraper

    @classmethod
    def get_episode_id(cls,show_id,season,ep_num):
        '''
        This is used to return an episode_id based on the show_id, season, and
        episode number.
        '''
        logger.info('Episode.get_episode_id: {} - {} - {}'.format(show_id,season,ep_num))

        # Look for the episode and the episode_id
        try:
            ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].episode_id

        # If we fail to find it, retrieve the episode
        except Exception as e:
            logger.error('get_episode_id - {}'.format(e))
            ret = None

        return ret

    @classmethod
    def get_imdb_info(cls,show_id,season):
        '''

        '''
        logger.info('Episode.get_imdb_info: {} - {}'.format(show_id,season))

        show_search = Show.get_show_name(show_id)
        show_imdb_id = Show.objects.get(show_id=show_id).imdb_id
        episodes = site_scraper.get_episodes_imdb_info(show_imdb_id,season)
        logger.info('\tepisode count: {}'.format(len(episodes)))

        for ep in episodes:
            logger.info('\tLOOP')
            logger.info('\t\t{} - {} - {}'.format(show_id,season,ep['ep_num']))
            try:
                ep_model = cls.objects.filter(show_id=show_id,season=season,ep_num=ep['ep_num'])[0]
            except Exception as e:
                logger.info('\tFailed to retrieve IMDB INFO: {}'.format(ep['ep_num']))
                logger.info('\texception: {}'.format(e))

            ep_model.imdb_id = ep['imdb_id']
            logger.info('\t\timdb_id={}'.format(ep_model.imdb_id))
            ep_model.imdb_name = ep['imdb_name']
            logger.info('\t\timdb_name={}'.format(ep_model.imdb_name))

            try:
                ep_model.full_clean()
            except ValidationError as v:
                logger.info('\tValidationError: {}'.format(v))
            except Exception as e:
                logger.info('\tException: {}'.format(e))
            else:
                ep_model.save()
                logger.info('\tepisode saved: {}'.format(ep_model.episode_id))

    @classmethod
    def get_count(cls,show_id,season):
        '''
        This is used to get the number of episodes present for a season.
        If the episodes are not present, they will be requested via the
        scraper and created in the db.
        '''
        logger.info('Episode.get_count: {} - {}'.format(show_id,season))

        # If we have episodes in the db, go ahead and return
        cnt = cls.objects.filter(show=show_id,season=season).count()
        logger.info('\tcount: {}'.format(cnt))
        if cnt:
            return cnt

        # If we don't have episodes, retrieve them
        show_imdb_id = Show.objects.get(show_id=show_id).imdb_id
        episodes = site_scraper.get_episodes_imdb_info(show_imdb_id,season)
        logger.info('\tretrieved episodes: {}'.format(len(episodes)))

        for ep in episodes:
            #logger.info('ep: {}'.format(ep))
            try:
                episode = cls(ep_num=str(ep['ep_num']),imdb_id=str(ep['imdb_id']),imdb_name=ep['imdb_name'],season=season,show_id=show_id).save()
            except DataError as d:
                raise ShowException('Invalid Season: '.format(season))

        cls.get_imdb_info(show_id,season)

        return cls.objects.filter(show=show_id,season=season).count()

    @classmethod
    def get_name(cls,show_id,season,ep_num):
        '''
        This is used to return an episode's name based on its show_id, season,
        and episode number.
        '''
        logger.info('Episode.get_name: {} - {} - {}'.format(show_id,season,ep_num))

        ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].imdb_name

        if (not ret):
            logger.info('\timdb_name not found')

            show_search = Show.get_show_name(show_id)
            show = Show.objects.get(show_id=show_id)
            logger.info('\tfound imdb_id: {}'.format(show.imdb_id))

            episodes = site_scraper.get_episodes_imdb_info(show.imdb_id,season)
            logger.info('\tepisode count: {}'.format(len(episodes)))

            for ep in episodes:
                ep_model = cls.objects.filter(show_id=show_id,season=season,ep_num=ep['ep_num'])[0]
                ep_model.imdb_id = ep['imdb_id']
                ep_model.imdb_name = ep['imdb_name']
                logger.info('ep_model: {}'.format(ep_model))

                try:
                    ep_model.full_clean()
                except ValidationError as v:
                    logger.info('\tValidationError: {}'.format(v))
                except Exception as e:
                    logger.info('\tException: {}'.format(e))
                else:
                    ep_model.save()
                    logger.info('\tepisode saved: {}'.format(ep_model.episode_id))

            ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].imdb_name

        return ret

    @classmethod
    def get_imdb_id(cls,show_id,season,ep_num):
        logger.info('Episode.get_imdb_id: {} - {} - {}'.format(show_id,season,ep_num))

        try:
            ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].imdb_id
            logger.info('\tfound: {}'.format(ret))
        except Exception as e:
            episode = cls.objects.filter(show=show_id,season=season,ep_num=ep_num)[0]
            cls.get_imdb_info(episode.show.show_id,episode.season)
            ret = cls.objects.filter(episode_id=episode_id,season=season,ep_num=ep_num)[0].imdb_id
            logger.info('\tretrieved: {}'.format(ret))

        return ret

    @classmethod
    def get_imdb_id_by_id(cls,episode_id):
        logger.info('Episode.get_imdb_id_by_id: {}'.format(episode_id))

        try:
            ret = cls.objects.filter(episode_id=episode_id)[0].imdb_id
            logger.info('\tfound: {}'.format(ret))
        except Exception:
            episode = cls.objects.filter(episode_id=episode_id)[0]
            cls.get_imdb_info(episode.show.show_id,episode.season)
            ret = cls.objects.filter(episode_id=episode_id)[0].imdb_id
            logger.info('\tretrieved: {}'.format(ret))

        return ret

    @classmethod
    def get_episodes(cls,show_id,season,cast=False):
        '''
        This method is responsible for returning an array of Episode objects
        which meet the show_id and season number passed.
        '''
        logger.info('Episode.get_episodes: {} - {} - {}'.format(show_id,season,cast))

        ep_filtered = cls.objects.filter(show_id=show_id,season=season).order_by('ep_num')
        logger.info('Episode.get_episodes: found {}'.format(ep_filtered.count()))

        episode_array = []
        for episode in ep_filtered:
            ep_cast_filtered =  Cast.objects.filter(episode_id=episode.episode_id)
            cast = [
                {
                    'actor': ep_cast_obj.actor,
                    'character': ep_cast_obj.character,
                }
                for ep_cast_obj in ep_cast_filtered
            ]
            episode_array.append({
                'episode_id': episode.episode_id,
                'ep_num': episode.ep_num,
                'ep_name': episode.imdb_name,
                'cast': cast,
            })
            logger.info('Episode.get_episodes: added - {}'.format(episode.imdb_name))

        return episode_array

class Cast(models.Model):
    cast_id = models.AutoField(primary_key=True)
    actor = models.CharField(max_length=100)
    character = models.CharField(max_length=100)
    episode_id = models.ForeignKey(Episode,on_delete=models.CASCADE)

    @classmethod
    def get_cast(cls,episode_id):
        logger.info('Cast.get_cast: {}'.format(episode_id))

        episode = Episode.objects.get(episode_id=episode_id)
        ret = cls.objects.filter(episode_id=episode)

        # If we get a 0 length return, fetch from the API
        castcount = len(ret)
        if (not castcount):
            logger.info('\tcastcount: {}'.format(castcount))

            try:
                imdb_id = Episode.get_imdb_id_by_id(episode_id)
                episode_obj = site_scraper.get_imdb_episode(imdb_id)
            except ElementNotFound as e:
                raise CastException('Unable to retrieve episode cast')

            # Build the cast entries from the API request
            ep_cast = episode_obj['crew']
            for cast in ep_cast:
                cast_model = cls(actor=cast['actor'],character=cast['character'],episode_id=episode)
                logger.info('Got model: {}'.format(cast_model))

                # In case the actor or character exceed DB limits
                try:
                    cast_model.full_clean()
                except ValidationError as v:
                    logger.info('\tValidationError: {}'.format(v))
                    logger.info('\tType: {}'.format(v.__class__.__name__))
                    logger.info('\tactor: {}'.format(cast_model.actor))
                    logger.info('\tcharacter: {}'.format(cast_model.character))
                except Exception as e:
                    logger.info('\tException: {}'.format(e))
                    logger.info('\tType: {}'.format(e.__class__.__name__))
                    logger.info('\tactor: {}'.format(cast_model.actor))
                    logger.info('\tcharacter: {}'.format(cast_model.character))
                else:
                    cast_model.save()
                    logger.info('\tcast saved: {}'.format(cast_model.cast_id))

            ret = cls.objects.filter(episode_id=episode)

        logger.info('\treturning: {}'.format(len(ret)))
        return ret

    @classmethod
    def get_match(cls,episode_id,term):
        logger.info('Cast.get_match: {}'.format(episode_id))
        cast = cls.get_cast(episode_id)
        logger.info('\tcast len: {}'.format(len(cast)))
        ret = False
        for entry in cast:
            #logger.info('cast_entry: {}'.format(entry))
            if (term in entry.actor or term in entry.character):
                logger.info('\tfound: {} - {}'.format(episode_id,entry.cast_id))
                ret = True
        logger.info('\treturning: {}'.format(ret))
        return ret

class ModelException(Exception):
    pass

class ShowException(ModelException):
    pass

class EpisodeException(ModelException):
    pass

class CastException(ModelException):
    pass
