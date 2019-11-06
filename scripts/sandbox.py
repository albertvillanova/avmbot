
import pywikibot
from collections import defaultdict

SITE = pywikibot.Site('wikidata', "wikidata")

def main():


    # site = pywikibot.Site('test', "wikidata")
    site = pywikibot.Site('wikidata', "wikidata")
    repo = site.data_repository()
    # item = pywikibot.ItemPage(repo, "Q121006")  # test:
    item = pywikibot.ItemPage(repo, 'Q4115189')  # Wikidata Sandbox

    # Add claim
    prop = 'P1082'
    claim = pywikibot.Claim(repo, prop)  # , rank='preferred')
    #value = to_value[insee_code]
    value = 6
    quantity = pywikibot.WbQuantity(value, site=site)
    #print(type(quantity))
    claim.setTarget(quantity)
    # TODO: Remove if population is not the last one
    # claim.setRank('preferred')
    item.addClaim(claim, summary="Adding population")
    #claim.changeRank('preferred')

    # Add qualifier
    point_in_time = 'P585'
    # TODO: REMOVE
    # point_in_time = 'P66'  # TEST
    qualifier = pywikibot.Claim(repo, point_in_time)
    # TODO: date
    date = pywikibot.WbTime(year=2015)  # , month=3, day=20)
    qualifier.setTarget(date)
    #claim.addQualifier(qualifier, summary=u'Adding a qualifier.')
    qualifier.isQualifier = True
    # set_qualifier
    claim.qualifiers[qualifier.getID()] = [qualifier]


    # Add source
    statedin = pywikibot.Claim(repo, 'P248')
    insee = pywikibot.ItemPage(repo, 'Q156616')
    statedin.setTarget(insee)
    statedin.isReference = True

    title = pywikibot.Claim(repo, 'P1476')
    text = pywikibot.WbMonolingualText("Recensement de la population 2015", 'fr')  # monolingual text
    title.setTarget(text)
    title.isReference = True

    publication_date = pywikibot.Claim(repo, 'P577')
    date = pywikibot.WbTime(year=2017, month=12, day=27)
    publication_date.setTarget(date)
    publication_date.isReference = True

    # claim.addSources([statedin, publication_date], summary="Adding sources.")
    # claim.addSources([statedin], summary="Adding sources.")
    #claim.addSources([statedin, title, publication_date], summary="Adding sources.")

    # set_source
    claims = [statedin, title, publication_date]
    source = defaultdict(list)
    for c in claims:
        source[c.getID()].append(c)
    claim.sources.append(source)


    claim.changeRank('preferred', summary="Add population 2015")

    """
~/pywiki/core/pywikibot/site.py in save_claim(self, claim, summary, bot)
   7709         if not claim.snak:
   7710             # We need to already have the snak value
-> 7711             raise NoPage(claim)
   7712         params = {'action': 'wbsetclaim',
   7713                   'claim': json.dumps(claim.toJSON()),

    Indeed, only after addClaim (wbcreateclaim), instead of first save_claim (wbsetclaim),
    an id is assigned to the Statement, and this is assigned to claim.snak
    
    claim.snak = data['claim']['id']
    """

def test_equality():
    item = pywikibot.ItemPage(SITE, 'Q4115189')  # Wikidata Sandbox
    _ = item.get()

    from add_population import *
    population_value = 6
    claim = create_claim(property=POPULATION, quantity=population_value)
    point_in_time = 'P585'
    date = {'year': 2015}
    point_in_time_claim = create_claim(property=point_in_time, **date)
    statement = set_qualifiers(claim, [point_in_time_claim])
    # Create sources
    stated_in = 'P248'
    insee = 'Q156616'
    stated_in_claim = create_claim(property=stated_in, item=insee)
    title = 'P1476'
    text = "Recensement de la population 2015"
    language = 'fr'
    title_claim = create_claim(property=title, text=text, language=language)
    publication_date = 'P577'
    date = {'year': 2017, 'month': 12, 'day': 27}
    publication_date_claim = create_claim(property=publication_date, **date)
    # Set sources
    statement = set_sources(statement,
                                       [stated_in_claim, title_claim, publication_date_claim])
    # Set rank
    statement.rank = 'preferred'

    if statement.getID() in item.claims:
        for claim in item.claims[statement.getID()]:
            print(claim.getTarget() == statement.getTarget())
            print(claim.getSources() == statement.getSources())
            print(claim.getRank() == statement.getRank())
            print(claim.qualifiers == statement.qualifiers)
            print(statement.qualifiers.keys())

            for k in statement.qualifiers.keys():
                print(k in claim.qualifiers)
                for q in statement.qualifiers[k]:
                    for q2 in claim.qualifiers[k]:
                        print('any?')
                        print(q.getTarget())
                        print(q.getTarget() == q2.getTarget())
                    print('end any')

    return False


if __name__ == '__main__':
    main()