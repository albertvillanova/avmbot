import pytest


@pytest.fixture(scope='session')
def wikidatabot():
    import wikidatabot
    wikidatabot.SITE = wikidatabot.pywikibot.Site('test', 'wikidata')
    wikidatabot.REPO = wikidatabot.SITE.data_repository()
    return wikidatabot
