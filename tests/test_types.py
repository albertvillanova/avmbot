
class TestClaim:

    def test_init(self, wikidatabot):
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


class TestItem:

    def test_init(self, wikidatabot):
        from wikidatabot.types import Item
        item_id = 'Q68'
        pywikibot_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, item_id)
        _ = pywikibot_item.get()
        item = Item(pywikibot_item)
        assert item.id == pywikibot_item.id
        assert item.labels == pywikibot_item.labels
        assert item.descriptions == pywikibot_item.descriptions
        assert item.aliases == pywikibot_item.aliases
        assert item.statements == pywikibot_item.claims
        assert item.sitelinks == pywikibot_item.sitelinks
