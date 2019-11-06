""""""

import pywikibot

# class Site:
#     _instance = None
#
#     def __init__(self, language='wikidata', family='wikidata'):
#         if Site._instance is None:
#             Site._instance = pywikibot.Site(language, fam=family)
#
#     def __getattr__(self, item):
#         return getattr(Site._instance, item)
#
#     def __setattr__(self, key, value):
#         return setattr(Site._instance, key, value)
#
#
# SITE = Site()

SITE = pywikibot.Site('wikidata', "wikidata")
REPO = SITE.data_repository()