"""Repository Pattern."""
from abc import ABC, abstractmethod

# TODO: import them directly here and remove from __init__
from wikidatabot import pywikibot, site, repo
from wikidatabot.types import Item


class Repository(ABC):
    """https://deviq.com/repository-pattern/"""
    @abstractmethod
    def get(self, id): pass
    # @abstractmethod
    def list(self): pass
    # @abstractmethod
    def add(self, entity): pass
    # @abstractmethod
    def delete(self, entity): pass
    # @abstractmethod
    def edit(self, entity): pass


class ItemPywikibotRepository(Repository):

    def __init__(self, repo=repo):
        self.repo = repo

    def get(self, item_id: str):
        pwb_item = pywikibot.ItemPage(self.repo, item_id)
        _ = pwb_item.get()
        # Renamed: statements = pwb_item.claims
        item = Item(id=pwb_item.id, labels=pwb_item.labels, descriptions=pwb_item.descriptions,
                    aliases=pwb_item.aliases, statements=pwb_item.claims, sitelinks=pwb_item.sitelinks)
        # pywikibot wrapper
        item._item = pwb_item
        return item


class PywikibotRepository:
    items = ItemPywikibotRepository()
