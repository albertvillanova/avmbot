import wikidatabot

wikidatabot.SITE = wikidatabot.pywikibot.Site('test', 'wikidata')
wikidatabot.REPO = wikidatabot.SITE.data_repository()


class TestClaim:

    def test_init(self):
        from wikidatabot.types import Claim
        claim_property = 'P115'  # 'P488'
        claim_item = 'Q271'  # 'Q50'
        claim = Claim(property=claim_property, item=claim_item)
        assert claim.property == claim_property
        assert isinstance(claim.value, wikidatabot.pywikibot.page.ItemPage)
        assert claim.value.getID() == claim_item
        assert isinstance(claim._claim, wikidatabot.pywikibot.page.Claim)
        assert claim._claim.repo._BaseSite__code == 'test'  # 'wikidata'
        assert claim._claim.repo._BaseSite__family.name == 'wikidata'
