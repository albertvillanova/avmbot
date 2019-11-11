import pytest


@pytest.fixture(scope='session')
def wikidatabot():
    import wikidatabot
    wikidatabot.site = wikidatabot.pywikibot.Site('test', 'wikidata')
    wikidatabot.repo = wikidatabot.site.data_repository()
    return wikidatabot
