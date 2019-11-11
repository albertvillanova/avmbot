import pywikibot
from wikidatabot.types import Claim


class TestClaim:

    def test_init(self):
        claim = Claim(property='P488', item='Q50')
        assert claim.property == 'P488'
        assert isinstance(claim.value, pywikibot.page.ItemPage)
        assert claim.value.getID() == 'Q50'
        assert isinstance(claim._claim, pywikibot.page.Claim)
        assert claim._claim.repo._BaseSite__code == 'wikidata'
        assert claim._claim.repo._BaseSite__family.name == 'wikidata'
