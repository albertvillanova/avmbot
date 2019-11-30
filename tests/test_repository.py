

class TestItemPywikibotRepository:

    # TODO: refactorize to assert result == expected, where expected is an instance of Item
    def test_get(self, wikidatabot):
        from wikidatabot.repository import ItemPywikibotRepository
        repository = ItemPywikibotRepository()
        item_id = 'Q68'
        item = repository.get(item_id)
        # expected:
        pwb_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, item_id)
        _ = pwb_item.get()
        assert item.id == pwb_item.id
        assert item.labels == pwb_item.labels
        assert item.descriptions == pwb_item.descriptions
        assert item.aliases == pwb_item.aliases
        assert item.statements == pwb_item.claims
        assert item.sitelinks == pwb_item.sitelinks
