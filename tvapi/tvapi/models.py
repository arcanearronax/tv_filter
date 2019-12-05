from django.db import models
from .api_service import *

import logging

logger = logging.getLogger('apilog')

class Show(models.Model):
    show_id = models.AutoField(primary_key=True)
    tmdb_id = models.IntegerField(null=True)
    tmdb_name = models.CharField(max_length=100,null=True)
    imdb_id = models.CharField(max_length=9,null=True)
    imdb_name = models.CharField(max_length=100,null=True)
    seasons = models.IntegerField(null=True)

    api_service = APIService

    @classmethod
    def get_show_name(cls,show_id):
        logger.info('Show.get_show_name: {}'.format(show_id))
        try:
            return cls.objects.get(show_id=show_id).tmdb_name
        except Exception as e:
            logger.info('get_show_name error: {}'.format(e))
            return None

    @classmethod
    def get_season_count(cls,show_id=show_id):
        logger.info('Show.get_season_count: {}'.format(show_id))
        try:
            return cls.objects.get(show_id=show_id).seasons
        except Exception as e:
            logger.info('get_season_count error: {}'.format(e))
            return None

    @classmethod
    def get_id_by_name(cls,show_search):
        logger.info('Show.get_show_id_by_name: {}'.format(show_search))

        ret = None
        try:
            # Return the show from db if we have a perfect match
            ret = cls.objects.get(tmdb_name=show_search)[0].show_id
            logger.info('\tperfect match found: {}'.format(show_id))
        except Exception as e:
            # Search for the show name via API
            logger.info('\tlooking for close match')
            showinfo = cls.api_service.get_show_tmdb_info(show_search)
            show_imdb_info = cls.api_service.get_show_imdb_info(show_search)

            # Parse out our dicts
            tmdb_id = showinfo['tmdb_id']
            tmdb_name = showinfo['tmdb_name']
            seasons = showinfo['seasons']
            imdb_id = show_imdb_info['imdb_id']
            imdb_name = show_imdb_info['imdb_name']

            try:
                # Search db for a perfect match to name from API
                show = cls.objects.filter(tmdb_id=tmdb_id,tmdb_name=tmdb_name)[0]
                logger.info('\tfound suspected match: {}'.format(show.show_id))
            except Exception:
                # Create a new db for the title from the API
                show = cls(tmdb_id=tmdb_id,tmdb_name=tmdb_name,seasons=seasons,imdb_id=imdb_id,imdb_name=imdb_name)
                show.save()
                logger.info('\tcreated: {}'.format(show.show_id))

            ret = show.show_id
            logger.info('\treturning: {}'.format(ret))

        return ret

class Episode(models.Model):
    episode_id = models.AutoField(primary_key=True)
    ep_num = models.IntegerField(null=True)
    tmdb_id = models.IntegerField(null=True)
    tmdb_name = models.CharField(null=True,max_length=100)
    imdb_id = models.CharField(null=True,max_length=9)
    imdb_name = models.CharField(null=True,max_length=100)
    show = models.ForeignKey(Show,on_delete=models.CASCADE)
    season = models.IntegerField()

    api_service = APIService

    @classmethod
    def get_episode_id(cls,show_id,season,ep_num):
        logger.info('Episode.get_episode_id: {} - {} - {}'.format(show_id,season,ep_num))
        ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].episode_id

        return ret

    @classmethod
    def get_imdb_info(cls,show_id,season):
        logger.info('Episode.get_imdb_info: {} - {}'.format(show_id,season))

        show_search = Show.get_show_name(show_id)
        show_imdb_id = Show.objects.get(show_id=show_id).imdb_id
        episodes = cls.api_service.get_episodes_imdb_info(show_imdb_id,season)
        logger.info('\tepisode count: {}'.format(len(episodes)))

        for ep in episodes:
            logger.info('\tLOOP')
            logger.info('\t\t{} - {} - {}'.format(show_id,season,ep['ep_num']))
            try:
                ep_model = cls.objects.filter(show_id=show_id,season=season,ep_num=ep['ep_num'])[0]
            except Exception as e:
                logger.info('\tFailed to retrieve IMDB INFO: {}'.format(ep['ep_num']))
                logger.info('\texception: {}'.format(e))
                pass
            ep_model.imdb_id = ep['imdb_id']
            logger.info('\t\timdb_id={}'.format(ep_model.imdb_id))
            ep_model.imdb_name = ep['imdb_name']
            logger.info('\t\timdb_name={}'.format(ep_model.imdb_name))
            ep_model.full_clean()
            ep_model.save()
            logger.info('\tepisode saved: {}'.format(ep_model.episode_id))

    @classmethod
    def get_count(cls,show_id,season):
        logger.info('Episode.get_count: {} - {}'.format(show_id,season))

        # If we have episodes in the db, go ahead and return
        cnt = cls.objects.filter(show=show_id,season=season).count()
        logger.info('\tcount: {}'.format(cnt))
        if cnt:
            return cnt

        # If we don't have episodes, retrieve them
        show_tmdb_id = Show.objects.get(show_id=show_id).tmdb_id
        episodes = cls.api_service.get_episodes(show_tmdb_id,season)
        logger.info('\tretrieved episodes: {}'.format(len(episodes)))

        for ep in episodes:
            #logger.info('ep: {}'.format(ep))
            episode = cls(ep_num=str(ep['ep_num']),tmdb_id=str(ep['tmdb_id']),tmdb_name=ep['tmdb_name'],season=season,show_id=show_id).save()

        cls.get_imdb_info(show_id,season)

        return cls.objects.filter(show=show_id,season=season).count()

    @classmethod
    def get_name(cls,show_id,season,ep_num):
        logger.info('Episode.get_name: {} - {} - {}'.format(show_id,season,ep_num))

        ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].imdb_name

        if (not ret):
            logger.info('\timdb_name not found')

            show_search = Show.get_show_name(show_id)
            show = Show.objects.get(show_id=show_id)
            logger.info('\tfound imdb_id: {}'.format(show.imdb_id))

            episodes = cls.api_service.get_episodes_imdb_info(show.imdb_id,season)
            logger.info('\tepisode count: {}'.format(len(episodes)))

            for ep in episodes:
                ep_model = cls.objects.filter(show_id=show_id,season=season,ep_num=ep['ep_num'])[0]
                ep_model.imdb_id = ep['imdb_id']
                ep_model.imdb_name = ep['imdb_name']
                logger.info('ep_model: {}'.format(ep_model))
                ep_model.full_clean()
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

class Cast(models.Model):
    cast_id = models.AutoField(primary_key=True)
    actor = models.CharField(max_length=100)
    character = models.CharField(max_length=100)
    episode_id = models.ForeignKey(Episode,on_delete=models.CASCADE)

    api_service = APIService

    @classmethod
    def get_cast(cls,episode_id):
        logger.info('Cast.get_cast: {}'.format(episode_id))

        try:
            episode = Episode.objects.get(episode_id=episode_id)
            logger.info('Got episode')
            ret = cls.objects.filter(episode_id=episode)
            logger.info('Got return')
        except ProgrammingError as p:
        #if (not len(ret)):
            logger.info('\tProgramming Error: {}'.format(p))

            imdb_id = Episode.get_imdb_id_by_id(episode_id)
            logger.info('\timdb_id: {}'.format(imdb_id))

            ep_cast = cls.api_service.get_episode_cast(imdb_id)
            logger.info('\tcast_len: {}'.format(len(ep_cast)))
            for cast in ep_cast:
                cast_model = cls(actor=cast['actor'],character=cast['character'],episode_id=episode)
                logger.info('Got model: {}'.format(cast_model))
                cast_model.full_clean()
                cast_model.save()
                logger.info('\tcast saved: {}'.format(cast_model.cast_id))
            ret = cls.objects.filter(episode_id=episode)
        else:
            logger.info('\treturning: {}'.format(len(ret)))
            return ret
        raise Exception('WOOLOOLOO')

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
