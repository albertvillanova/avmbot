from types import SimpleNamespace

import pytest

# Add scripts directory to sys.path
# TODO: all script interesting functionalities should be moved to wikidatabot
from pathlib import Path
import sys
scripts_directory = Path.cwd() / 'scripts'
sys.path.insert(0, str(scripts_directory))

# wikidata, wikidata
# Do a test edit to Wikidata
# testqid = 'Q4115189' # Wikidata sandbox
# testproperty = 'P31' # instance of
# testvalue = 'Q3938'  # Sandbox


# @pytest.fixture(scope='session')
# class P(SimpleNamespace):
#     APPOINTED_BY = 'P748'


@pytest.fixture(scope='session')
def wikidatabot():
    import wikidatabot
    wikidatabot.site = wikidatabot.pywikibot.Site('test', 'wikidata')
    wikidatabot.repo = wikidatabot.site.data_repository()
    return wikidatabot
