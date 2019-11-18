
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

    def test_init_from_pwb_item(self, wikidatabot):
        from wikidatabot.types import Item
        item_id = 'Q68'
        pwb_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, item_id)
        _ = pwb_item.get()
        item = Item.from_pwb(pwb_item)
        assert item.id == pwb_item.id
        assert item.labels == pwb_item.labels
        assert item.descriptions == pwb_item.descriptions
        assert item.aliases == pwb_item.aliases
        assert item.statements == pwb_item.claims
        assert item.sitelinks == pwb_item.sitelinks

    def test_init_from_id(self, wikidatabot):
        from wikidatabot.types import Item
        item_id = 'Q68'
        item = Item.from_pwb(item_id)
        # expected:
        pwb_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, item_id)
        _ = pwb_item.get()
        assert item.id == pwb_item.id
        assert item.labels == pwb_item.labels
        assert item.descriptions == pwb_item.descriptions
        assert item.aliases == pwb_item.aliases
        assert item.statements == pwb_item.claims
        assert item.sitelinks == pwb_item.sitelinks
