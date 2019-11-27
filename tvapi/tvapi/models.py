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
        try:
            return cls.objects.get(show_id=show_id).tmdb_name
        except Exception as e:
            logger.info('get_show_name error: {}'.format(e))
            return None

    @classmethod
    def get_season_count(cls,show_id=show_id):
        try:
            return cls.objects.get(show_id=show_id).seasons
        except Exception as e:
            logger.info('get_season_count error: {}'.format(e))
            return None

    @classmethod
    def get_id_by_name(cls,show_search):
        logger.info('get_show_id: {}'.format(show_search))

        ret = None
        try:
            # Return the show if we have a perfect match
            ret = cls.objects.get(tmdb_name=show_search)[0].show_id
        except Exception as e:
            # Search for the show name via API
            logger.info('show_id_error: {}'.format(e))
            showinfo = cls.api_service.get_show_tmdb_info(show_search)
            show_imdb_info = cls.api_service.get_show_imdb_info(show_search)

            # Parse out our dicts
            tmdb_id = showinfo['tmdb_id']
            tmdb_name = showinfo['tmdb_name']
            seasons = showinfo['seasons']
            imdb_id = show_imdb_info['imdb_id']
            imdb_name = show_imdb_info['imdb_name']

            try:
                # Search db for a perfect match
                show = cls.objects.filter(tmdb_id=tmdb_id,tmdb_name=tmdb_name)[0]
            except Exception:
                # Create a new db entry
                show = cls(tmdb_id=tmdb_id,tmdb_name=tmdb_name,seasons=seasons,imdb_id=imdb_id,imdb_name=imdb_name)
                logger.info('SHOW HERE: {}'.format(show))
                show.save()

            ret = show.show_id

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
        try:
            return cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].episode_id
        except:
            return -1

    @classmethod
    def get_imdb_info(cls,show_id,season):
        show_search = Show.get_show_name(show_id)
        show_imdb_id = Show.objects.get(show_id=show_id).imdb_id
        episodes = cls.api_service.get_episodes_imdb_info(show_imdb_id,season)
        logger.info('EPISODES: {}'.format(episodes))

        for ep in episodes:
            ep_model = cls.objects.filter(show_id=show_id,season=season,ep_num=ep['ep_num'])[0]
            ep_model.imdb_id = ep['imdb_id']
            ep_model.imdb_name = ep['imdb_name']
            logger.info('ep_model: {}'.format(ep_model))
            ep_model.full_clean()
            ep_model.save()

    @classmethod
    def get_count(cls,show_id,season):

        # If we have episodes, go ahead and return
        cnt = cls.objects.filter(show=show_id,season=season).count()
        if cnt:
            return cnt

        # If we don't have episodes, retrieve them
        logger.info('showwwwww: {}'.format(Show.objects.get(show_id=show_id)))
        show_tmdb_id = Show.objects.get(show_id=show_id).tmdb_id
        episodes = cls.api_service.get_episodes(show_tmdb_id,season)
        print('episodes_class: {}'.format(episodes))

        for ep in episodes:
            logger.info('ep: {}'.format(ep))
            episode = cls(ep_num=str(ep['ep_num']),tmdb_id=str(ep['tmdb_id']),tmdb_name=ep['tmdb_name'],season=season,show_id=show_id).save()

        return cls.objects.filter(show=show_id,season=season).count()

    @classmethod
    def get_name(cls,show_id,season,ep_num):
        logger.info('get_name: {} - {} - {}'.format(show_id,season,ep_num))

        ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].imdb_name

        #if (not ret):
        #    ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].tmdb_name

        if (not ret):
            logger.info('imdb_name not found')
            show_search = Show.get_show_name(show_id)
            show = Show.objects.get(show_id=show_id)
            logger.info('Found IMDB ID: {}'.format(show.imdb_id))
            show_imdb_id = show.imdb_id
            episodes = cls.api_service.get_episodes_imdb_info(show_imdb_id,season)
            logger.info('EPISODES: {}'.format(episodes))

            #episode = cls(ep_num=ep_num,imdb_id=ep_info['imdb_id'],imdb_name=ep_info['imdb_name'],season=season,show_id=show_id)
            #episode.save()

            for ep in episodes:
                logger.info('EP Type: {}'.format(ep))
                ep_model = cls.objects.filter(show_id=show_id,season=season,ep_num=ep['ep_num'])[0]
                ep_model.imdb_id = ep['imdb_id']
                ep_model.imdb_name = ep['imdb_name']
                logger.info('ep_model: {}'.format(ep_model))
                ep_model.full_clean()
                ep_model.save()

            ret = cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].imdb_name

        return ret

    @classmethod
    def get_imdb_id(cls,show_id,season,ep_num):
        logger.info('get_imdb_info: {} - {} - {}'.format(show_id,season,ep_num))

        try:
            return cls.objects.filter(show_id=show_id,season=season,ep_num=ep_num)[0].imdb_id
        except Exception as e:
            episode = cls.objects.filter(show=show_id,season=season,ep_num=ep_num)[0]
            cls.get_imdb_info(episode.show.show_id,episode.season)
            return cls.objects.filter(episode_id=episode_id,season=season,ep_num=ep_num)

    @classmethod
    def get_imdb_id_by_id(cls,episode_id):
        try:
            return cls.objects.filter(episode_id=episode_id)[0].imdb_id
        except Exception:
            episode = cls.objects.filter(episode_id=episode_id)[0]
            cls.get_imdb_info(episode.show.show_id,episode.season)
            return cls.objects.filter(episode_id=episode_id)[0].imdb_id



class Cast(models.Model):
    cast_id = models.AutoField(primary_key=True)
    actor = models.CharField(max_length=100)
    character = models.CharField(max_length=100)
    episode_id = models.ForeignKey(Episode,on_delete=models.CASCADE)

    api_service = APIService

    @classmethod
    def get_cast(cls,episode_id):
        episode = Episode.objects.get(episode_id=episode_id)
        try:
            ret = cls.objects.filter(episode_id=episode)
        except Exception:
            imdb_id = Episode.get_imdb_id_by_id(episode_id)
            ep_cast = cls.api_service.get_episode_cast(imdb_id)
            for cast in ep_cast:
                cast_model = cls(actor=cast['actor'],character=cast['character'],episode_id=episode)
                cast_model.full_clean()
                cast_model.save()
            ret = cls.objects.filter(episode_id=episode)
        return ret

    @classmethod
    def get_match(cls,episode_id,term):
        cast = cls.get_cast(episode_id)
        logger.info('CAST: {}'.format(cast))
        ret = False
        for entry in cast:
            logger.info('cast_entry: {}'.format(entry))
            if (term in entry.actor or term in entry.character):
                ret = True
        return ret
