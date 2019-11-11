""""""
from collections import defaultdict, OrderedDict
import copy
import pywikibot

from wikidatabot import SITE, REPO


# class Site:
#     _instance = None
#
#     def __init__(self, language='wikidata', family='wikidata'):
#         if Site._instance is None:
#             Site._instance = pywikibot.Site(language, fam=family)
#
#     def __getattr__(self, item):
#         return getattr(Site._instance, item)
#
#     def __setattr__(self, key, value):
#         return setattr(Site._instance, key, value)
#
#
# SITE = Site()
# REPO = SITE.get_repo()


class Claim:

    def __init__(self, property=None, value=None, item=None, quantity=None,
                     year=None, month=None, day=None, text=None, language=None):
        self.property = property
        if item is not None:
            value = pywikibot.ItemPage(REPO, item)
        elif quantity is not None:
            value = pywikibot.WbQuantity(quantity, site=SITE)
        elif year is not None:
            value = pywikibot.WbTime(year=year, month=month, day=day)
        elif text is not None:
            if language is not None:
                value = pywikibot.WbMonolingualText(text, language)
        self.value = value

        claim = pywikibot.Claim(REPO, property)
        claim.setTarget(value)
        self._claim = claim

    @property
    def property(self):
        return self._property

    @property.setter
    def property(self, property):
        self._property = property

    # def __getattr__(self, item):
    #     return getattr(self.claim, item)
    #
    # def __setattr__(self, key, value):
    #     return setattr(self.claim, key, value)

    def create_claim(property=None, value=None, item=None, quantity=None,
                     year=None, month=None, day=None, text=None, language=None):

        claim = pywikibot.Claim(REPO, property)

        if item is not None:
            value = pywikibot.ItemPage(REPO, item)
        elif quantity is not None:
            value = pywikibot.WbQuantity(quantity, site=SITE)
        elif year is not None:
            value = pywikibot.WbTime(year=year, month=month, day=day)
        elif text is not None:
            if language is not None:
                value = pywikibot.WbMonolingualText(text, language)

        claim.setTarget(value)

        return claim


class Qualifier(Claim):
    pass


class QualifierContainer(OrderedDict):
    """TODO: OrderedDefaultDict(list)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def __missing__(self, key):
        self[key] = value = []
        return value
    def add_qualifier(self, qualifier: Qualifier):
        self[qualifier.property_id].append(qualifier)


class Source(Claim):
    pass


class SourceContainer:
    pass


class Statement:
    """TODO"""
    def __init__(self, claim: Claim = None, rank='normal',
                 qualifiers=None, sources=None):
                 # qualifiers: QualifierContainer = None, sources: SourceContainer = None):
        self.claim = claim
        self.rank = rank
        self.qualifiers = qualifiers
        self.sources = sources

        self._statement = copy.deepcopy(claim._claim)
        self.set_rank(rank)
        if qualifiers is not None:
            self.set_qualifiers(qualifiers)
        if sources is not None:
            self.set_sources(sources)

    @property
    def claim(self):
        return self._claim

    @claim.setter
    def claim(self, claim):
        self._claim = claim

    def set_rank(self, rank):
        self._statement.rank = rank

    def set_qualifiers(self, qualifiers):
        # def set_qualifiers(claim, qualifiers):
        #     for qualifier in qualifiers:
        #         qualifier.isQualifier = True
        #         claim.qualifiers[qualifier.getID()] = [qualifier]
        #     return claim
        for qualifier in qualifiers:
            qualifier_claim = qualifier._claim
            qualifier_claim.isQualifier = True
            self._statement.qualifiers[qualifier_claim.getID()] = [qualifier_claim]

    def set_sources(self, sources):
        # def set_sources(claim, sources):
        #     source_group = defaultdict(list)
        #     for source in sources:
        #         source.isReference = True
        #         source_group[source.getID()].append(source)
        #     claim.sources.append(source_group)
        #     return claim
        source_group = defaultdict(list)
        for source in sources:
            source_claim = source._claim
            source_claim.isReference = True
            source_group[source_claim.getID()].append(source_claim)
        self._statement.sources.append(source_group)


class Item:
    """TODO"""

    def __init__(self, item=None):
        self._item = item

    def add_statement(self, statement: Statement = None, summary=None):
        if statement is None:
            return

        # def add_statement(item, statement, summary=SUMMARY, repo=REPO):
        #     """
        #
        #     :param item:
        #     :param statement:
        #     :param summary:
        #     :param repo:
        #     :return:
        #     """
        #     if not isinstance(item, str):
        #         item_id = item.getID()
        #     else:
        #         item_id = item
        #         item = pywikibot.ItemPage(repo, item_id)
        #         _ = item.get()
        #
        #     # Checks
        #
        #     # Create item statement
        #     identification = {'id': item_id}
        #     # TODO: []
        #     data = {'claims': [statement.toJSON()]}  # add the statement on property: use []
        #     # to overwrite statement on property: do not use []
        #     response = repo.editEntity(identification, data, summary=summary)
        #     return response

        if not isinstance(self._item, str):
            item_id = self._item.getID()
        # else:
        #     item_id = item
        #     item = pywikibot.ItemPage(repo, item_id)
        #     _ = item.get()

        # Create item statement
        identification = {'id': item_id}
        # TODO: []
        data = {'claims': [statement._statement.toJSON()]}  # add the statement on property: use []
        # to overwrite statement on property: do not use []  # FALSE; use snak instead
        response = REPO.editEntity(identification, data, summary=summary)
        return response
