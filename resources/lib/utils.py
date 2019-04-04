#!/usr/bin/python
# coding: utf8

import xbmcvfs, xbmcgui, xbmc
import os
from resources.lib.helper import *

RESET_VALUE = '0'
THUMBSUP_VALUE_SETTING_ID = 'ThumbsUpRateValue'
THUMBSDOWN_VALUE_SETTING_ID = 'ThumbsDownRateValue'
NEW_TAG = 'mylist'
WIN = xbmcgui.Window(10000)


def ismylist(params):
    item_id, item_type = get_idandtype()
    item_tags = get_tags(item_id, item_type)
    if item_tags:
        # if in my list -> set window property
        if NEW_TAG in item_tags:
            WIN.setProperty("IsInMyList", item_id)


def togglemylist(params):
    item_id, item_type = get_idandtype()
    item_tags = get_tags(item_id, item_type)
    if item_tags:
        # remove NEW_TAG
        if NEW_TAG in item_tags:
            item_tags.remove(NEW_TAG)
        # NEW_TAG not in list - let's add it
        else:
            item_tags.append(NEW_TAG)
            WIN.setProperty("IsInMyList", item_id)
        json_call('VideoLibrary.Set' + item_type + 'Details',
                  params={item_type + 'id': int(item_id),
                          'tag': item_tags})

def ratetitle(params):
    action = params.get("rateaction")
    action_dict = {'like': xbmc.getInfoLabel("Skin.String(%s)" % THUMBSUP_VALUE_SETTING_ID),
                   'dislike': xbmc.getInfoLabel("Skin.String(%s)" % THUMBSDOWN_VALUE_SETTING_ID),
                   'reset': RESET_VALUE}
    if action in action_dict and int(action_dict[action]) >= 0:
        item_id, item_type = get_idandtype()
        if item_id and item_type:
            json_call('VideoLibrary.Set' + item_type + 'Details',
                      params={item_type + 'id': int(item_id),
                              'userrating': int(action_dict[action])})
            WIN.setProperty("RateTitle", item_id)
            WIN.setProperty("RateTitle.Action", action)

def gettvshowid(params):
    """extracts tvshowid from kodidb"""
    episode_query = json_call('VideoLibrary.GetEpisodeDetails',
                              properties=['tvshowid'],
                              params={'episodeid': int(params.get('dbid'))})
    try:
        tvshow_id = str(episode_query['result']['episodedetails']['tvshowid'])
        output = params.get("output", "ListItem.TVShowID")
        WIN.setProperty(output, tvshow_id)
    except Exception:
        log('Could not get the TV show ID')
        return

def playtrailer(params):
    """auto play first youtube trailer windowed/fullscreen, tvshows local grab integrated
            (will later seperate methods)"""
    if not visible("!String.IsEmpty(Window(Home).Property(traileractionbusy)) "
                             "| Window.IsActive(busydialog)"):
        title = params.get("title", "")
        trailer_mode = params.get("mode", "windowed").replace("auto_", "")
        local = params.get("local", "") == "true"
        allow_local_tv_show = params.get("tvshow", "") == "true"
        item_control_id = params.get("control", "System.CurrentControlID")
        allow_youtube = params.get("youtube", "true") == "true"
        list_item_title = xbmc.getInfoLabel("ListItem.Title")
        local_language = ""
        if local:
            local_language = " " + xbmc.getInfoLabel("System.Language").decode('utf-8')
        li_trailer = ""

        if allow_local_tv_show:
            item_path = xbmc.getInfoLabel(
                'Container({}).ListItem().Path'.format(xbmc.getInfoLabel('%s' % item_control_id)))
            if not item_path:
                item_path = xbmc.getInfoLabel(
                    'Container({}).ListItem.Property(originalpath)'.format(
                        xbmc.getInfoLabel('%s' % item_control_id)))
            folder_name = xbmc.getInfoLabel(
                'Container({}).ListItem().FolderName'.format(xbmc.getInfoLabel('%s' % item_control_id)))
            if item_path:
                files = xbmcvfs.listdir(item_path)[1]
                for filename in files:
                    folder_name_trailer = folder_name.lower() + "-trailer"
                    file_name_noext = os.path.splitext(filename)[0].lower()
                    if file_name_noext.endswith("-trailer") and \
                            (file_name_noext == "tvshow-trailer" or file_name_noext == folder_name_trailer):
                        li_trailer = os.path.join(item_path, filename)

        if not li_trailer and title and allow_youtube \
                and not visible("Container.Scrolling | Container.OnNext"
                                          " | Container.OnPrevious | Player.HasVideo"):
            tvshow_str = ""
            if allow_local_tv_show:
                tvshow_str = " tv show"
            li_trailer = get_first_youtube_video("%s%s%s trailer" % (title, tvshow_str, local_language))

        WIN.setProperty("traileractionbusy", "traileractionbusy")
        if li_trailer and not visible("Container.Scrolling | Container.OnNext "
                                                "| Container.OnPrevious | Player.HasVideo") \
                and list_item_title == xbmc.getInfoLabel("ListItem.Title"):
            if trailer_mode == "fullscreen" or trailer_mode == "background":
                xbmc.executebuiltin('PlayMedia("%s")' % li_trailer)
            else:
                xbmc.executebuiltin('PlayMedia("%s",1)' % li_trailer)
            WIN.setProperty("TrailerPlaying", trailer_mode)
        WIN.clearProperty("traileractionbusy")
