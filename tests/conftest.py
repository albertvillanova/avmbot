import pytest


# wikidata, wikidata
# Do a test edit to Wikidata
# testqid = 'Q4115189' # Wikidata sandbox
# testproperty = 'P31' # instance of
# testvalue = 'Q3938'  # Sandbox


@pytest.fixture(scope='session')
def wikidatabot():
    import wikidatabot
    wikidatabot.site = wikidatabot.pywikibot.Site('test', 'wikidata')
    wikidatabot.repo = wikidatabot.site.data_repository()
    return wikidatabot
