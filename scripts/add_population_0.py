"""

add_population.py -y 2015 -t regions -l > log_regions.log
"""

import argparse
from collections import defaultdict
import pandas as pd
import pywikibot
from pywikibot import pagegenerators as pg
import os

# Constants
POPULATION = 'P1082'
POINT_IN_TIME = 'P585'

# To load data
URL = 'https://www.insee.fr/fr/statistiques/fichier/3292622/ensemble.xls'
URL = '~/share/data/insee/ensemble.xls'
URL = os.path.expanduser(URL)
SHEET_NAME = 'Régions'
INDEX = 'Code région'
COLUMN = 'Population municipale'

SITE = pywikibot.Site('wikidata', "wikidata")
REPO = SITE.data_repository()

INSTANCE_OF = 'P31'
SUBCLASS = 'P279'
END_TIME = 'P582'
# TODO: Only one
# QUERY = """
# SELECT ?item WHERE {
#     ?item wdt:{instance_of} wd:{administrative_division}.
# }
# """.replace('{instance_of}', INSTANCE_OF)

QUERY = ("""
    SELECT ?item WHERE {
        ?item wdt:{instance_of}/wdt:{subclass}* wd:{administrative_division}.
        FILTER NOT EXISTS {
            ?item p:{instance_of} ?instance_statement.
            ?instance_statement pq:{end_time} ?end_time_date.
        }
    }
""".replace('{instance_of}', INSTANCE_OF)
    .replace('{subclass}', SUBCLASS)
    .replace('{end_time}', END_TIME)
    .replace('{population}', POPULATION)
    .replace('{point_in_time}', POINT_IN_TIME)
)

_ = """
    FILTER NOT EXISTS {
        ?item wdt:{instance_of} wd:{administrative_division}.
        ?item p:{population} ?population_statement.
        ?population_statement pq:{point_in_time} ?date.
        FILTER(YEAR(?date) = {year})
    }
"""

CUSTOM_QUERY_ADDED_INSEE_CODE = ("""
SELECT ?item WHERE {
    ?item wdt:{instance_of} wd:{administrative_division}.
    ?item p:{insee_code} ?insee_code_statement.
    ?insee_code_statement pq:{point_in_time} ?date.
        FILTER(YEAR(?date) = {year})
}
""".replace('{instance_of}', INSTANCE_OF)
    .replace('{point_in_time}', POINT_IN_TIME)
    .replace('{year}', '2017')
)


CORRECTED_QUERY_FOR_COMMUNES = """
# ?itemLabel
SELECT DISTINCT ?item WHERE {
  ?item wdt:P31/wdt:P279* wd:Q484170.
  OPTIONAL {
    ?item p:P31 [pq:P582 ?end_time_date].
    }
  FILTER(IF(BOUND(?end_time_date), YEAR(?end_time_date) >= 2017, true))
  OPTIONAL {
    ?item p:P31 [pq:P580 ?start_time_date].
  }
  FILTER(IF(BOUND(?start_time_date), YEAR(?start_time_date) < 2017, true))
# Not working: keeps items that besides 2015 have population for another date
#  OPTIONAL {
#    ?item p:P1082 [pq:P585 ?point_in_time_date].
#  }
#  FILTER(IF(BOUND(?point_in_time_date), YEAR(?point_in_time_date) != 2015, true))
  MINUS {
    ?item p:P1082 [pq:P585 ?point_in_time_date].
    FILTER(YEAR(?point_in_time_date) = 2015)
  }
#  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
  }
#LIMIT 10 

"""
# 3
CORRECTED_QUERY_FOR_COMMUNES = """
# ?itemLabel
SELECT DISTINCT ?item WHERE {
  # ?item wdt:P31/wdt:P279* wd:Q484170.
  # OPTIONAL {
  #   ?item p:P31 [pq:P582 ?end_time_date].
  #   }
  ?item p:P31/p:P279* ?st.
  ?st ps:P31/ps:P279* wd:Q484170. 
  OPTIONAL{?st pq:P582 ?end_time_date}
  FILTER(IF(BOUND(?end_time_date), YEAR(?end_time_date) >= 2017, true))
  # OPTIONAL {
  #   ?item p:P31 [pq:P580 ?start_time_date].
  # }
  OPTIONAL{?st pq:P580 ?start_time_date}
  FILTER(IF(BOUND(?start_time_date), YEAR(?start_time_date) < 2017, true))
# Not working: keeps items that besides 2015 ahve population for another date
#  OPTIONAL {
#    ?item p:P1082 [pq:P585 ?point_in_time_date].
#  }
#  FILTER(IF(BOUND(?point_in_time_date), YEAR(?point_in_time_date) != 2015, true))
  MINUS {
    ?item p:P1082 [pq:P585 ?point_in_time_date].
    FILTER(YEAR(?point_in_time_date) = 2015)
  }
#  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
  }
#LIMIT 10 
"""


# 4
CORRECTED_QUERY_FOR_COMMUNES = """
# ?itemLabel
SELECT DISTINCT ?item WHERE {
  # ?item wdt:P31/wdt:P279* wd:Q484170.
  # OPTIONAL {
  #   ?item p:P31 [pq:P582 ?end_time_date].
  #   }
  ?item p:P31/p:P279* ?st.
  ?st ps:P31/ps:P279* wd:Q484170. 
  OPTIONAL{?st pq:P582 ?end_time_date}
  FILTER(IF(BOUND(?end_time_date), YEAR(?end_time_date) >= 2017, true))
  # OPTIONAL {
  #   ?item p:P31 [pq:P580 ?start_time_date].
  # }
  OPTIONAL{?st pq:P580 ?start_time_date}
  FILTER(IF(BOUND(?start_time_date), YEAR(?start_time_date) < 2017, true))
# Not working: keeps items that besides 2015 ahve population for another date
#  OPTIONAL {
#    ?item p:P1082 [pq:P585 ?point_in_time_date].
#  }
#  FILTER(IF(BOUND(?point_in_time_date), YEAR(?point_in_time_date) != 2015, true))
  FILTER NOT EXISTS {
    ?item p:P1082 [pq:P585 ?point_in_time_date].
    FILTER(YEAR(?point_in_time_date) = 2015)
  }
#  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
  }
#LIMIT 10 
"""

# 5: communes nouvelles starting at 2017-01-01
CORRECTED_QUERY_FOR_COMMUNES = """
# ?itemLabel
SELECT DISTINCT ?item WHERE {
  ?item p:P31 ?st .
  ?st ps:P31 wd:Q2989454 .
  OPTIONAL{?st pq:P582 ?end_time_date}
  FILTER(IF(BOUND(?end_time_date), YEAR(?end_time_date) >= 2017, true))
  ?st pq:P580 ?start_time_date .
  FILTER(YEAR(?start_time_date) = 2017)
  FILTER NOT EXISTS {
    ?item p:P1082 [pq:P585 ?point_in_time_date].
    FILTER(YEAR(?point_in_time_date) = 2015)
  }
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
}
# LIMIT 10
"""

# 6: communes associées ou déléguées [communes_ass_del]
CORRECTED_QUERY_FOR_COMMUNES = """
# ?itemLabel
SELECT DISTINCT ?item WHERE {
  ?item p:P31 ?st .
  ?st ps:P31 ?instance_of
  VALUES ?instance_of {wd:Q666943 wd:Q21869758}.
  
  OPTIONAL{?st pq:P580 ?start_time_date}
  # FILTER(IF(BOUND(?start_time_date), YEAR(?start_time_date) < 2017, true))
  FILTER(IF(BOUND(?start_time_date), ?start_time_date <= "2017-01-01"^^xsd:dateTime, true))
  
  OPTIONAL{?st pq:P582 ?end_time_date}
  # FILTER(IF(BOUND(?end_time_date), YEAR(?end_time_date) >= 2017, true))
  FILTER(IF(BOUND(?end_time_date), ?end_time_date > "2017-01-01"^^xsd:dateTime, true))
  
  FILTER NOT EXISTS {
    ?item p:P1082 [pq:P585 ?point_in_time_date].
    FILTER(YEAR(?point_in_time_date) = 2015)
  }
  # SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
}
# LIMIT 10
"""

# 6: communes associées ou déléguées [communes_ass_del]
CUSTOM_QUERY_FOR_COMS = """
# ?itemLabel
SELECT DISTINCT ?item WHERE {
  ?item wdt:{insee_code} ?insee_code_value .
  VALUES ?insee_code_value {"97501" "97502" "97701" "97801"} .

  # SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
}
# LIMIT 10
"""

SUMMARY = "Add 2015 population"

CHECK_QUERY = ("""
SELECT ?item WHERE {
    ?item wdt:{instance_of} wd:{administrative_division}.
    ?item p:{population} ?population_statement.
    ?population_statement pq:{point_in_time} ?date.
    FILTER(YEAR(?date) = {year})
    FILTER NOT EXISTS {
        ?item p:{instance_of} ?instance_statement.
        ?instance_statement pq:{end_time} ?end_time_date
    }
}
""".replace('{instance_of}', INSTANCE_OF)
    .replace('{end_time}', END_TIME)
    .replace('{population}', POPULATION)
    .replace('{point_in_time}', POINT_IN_TIME)
)


PARAMS = {
    'regions': {
        'administrative_division': 'Q36784',  # region of France
        'insee_code': 'P2585',  # INSEE region code
        'sheet_name': 'Régions',
        'index': 'Code région',
        'column': 'Population municipale',
    },
    'departements': {
        'administrative_division': 'Q6465',  # department of France
        'insee_code': 'P2586',  # INSEE department code
        'sheet_name': 'Départements',
        'index': 'Code département',
        'column': 'Population municipale',
    },
    # 'droms': They are already included in regions
    'arrondissements': {
        'administrative_division': 'Q194203',  # arrondissement of France
        'insee_code': 'P3423',  # INSEE arrondissement code
        'sheet_name': 'Arrondissements',
        'index': ['Code département', 'Code arrondissement'],
        'column': 'Population municipale',
    },
    'cantons': {
        'administrative_division': 'Q18524218',  # canton of France (starting March 2015)
        'insee_code': 'P2506',  # INSEE canton code
        'sheet_name': 'Cantons et métropoles',
        'index': ['Code département', 'Code canton'],
        'column': 'Population municipale',
    },
    'communes': {
        'administrative_division': 'Q484170',  # commune of France
        'insee_code': 'P374',  # INSEE municipality code
        'sheet_name': 'Communes',
        'index': ['Code département', 'Code commune'],
        'column': 'Population municipale',
    },
    'communes_ass_del': {
        'administrative_division': 'Q484170',  # commune of France
        'insee_code': 'P374',  # INSEE municipality code
        'sheet_name': 'Communes associées ou déléguées',
        'index': ['Code département', 'Code commune'],
        'column': 'Population municipale',
    },
    'coms': {
        'administrative_division': 'Q484170',  # commune of France
        'insee_code': 'P374',  # INSEE municipality code
        'sheet_name': "Collectivités d'outre-mer",
        'index': ['Code collectivité', 'Code commune'],
        'column': 'Population municipale',
    },
}

YEAR = '2015'
TO = 'REGIONS'
IS_LAST = False
DEBUG = True


def parse_args():
    parser = argparse.ArgumentParser(description="Add population")
    parser.add_argument('-y', '--year', required=True)
    parser.add_argument('-t', '--to', default='regions')
    parser.add_argument('-l', '--is-last', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--check', action='store_true')

    args = parser.parse_args()
    return args


def load_data(url=URL, sheet_name=SHEET_NAME, index=INDEX, column=COLUMN, **kwargs):
    if isinstance(index, str):
        to_dtype = {index: str}
    else:
        to_dtype = {idx: str for idx in index}
    df = pd.read_excel(url, sheet_name=sheet_name, header=7, dtype=to_dtype)
    if isinstance(index, str):
        df = df.set_index(index)
    else:
        df['code'] = df[index[0]]
        for idx in index[1:]:
            df['code'] += df[idx]
        # Correct code for communes in Guadeloupe, Martinique, Guyane, La Réunion: remove repeated digit
        df['code'] = df['code'].where(df['code'].str.len() < 6, df['code'].str[:3] + df['code'].str[4:])
        df = df.set_index('code')
    to_value = df[column].to_dict()
    return to_value


def create_claim(property=None, value=None, item=None, quantity=None,repo=REPO, site=SITE,
                 year=None, month=None, day=None, text=None, language=None):

    claim = pywikibot.Claim(repo, property)

    if item is not None:
        value = pywikibot.ItemPage(repo, item)
    elif quantity is not None:
        value = pywikibot.WbQuantity(quantity, site=site)
    elif year is not None:
        value = pywikibot.WbTime(year=year, month=month, day=day)
    elif text is not None:
        if language is not None:
            value = pywikibot.WbMonolingualText(text, language)

    claim.setTarget(value)

    return claim


def set_qualifiers(claim, qualifiers):
    for qualifier in qualifiers:
        qualifier.isQualifier = True
        claim.qualifiers[qualifier.getID()] = [qualifier]
    return claim


def set_sources(claim, sources):
    source_group = defaultdict(list)
    for source in sources:
        source.isReference = True
        source_group[source.getID()].append(source)
    claim.sources.append(source_group)
    return claim


def add_statement(item, statement, summary=SUMMARY, repo=REPO):
    """

    :param item:
    :param statement:
    :param summary:
    :param repo:
    :return:
    """
    if not isinstance(item, str):
        item_id = item.getID()
    else:
        item_id = item
        item = pywikibot.ItemPage(repo, item_id)
        _ = item.get()

    # Checks

    # Create item statement
    identification = {'id': item_id}
    # TODO: []
    data = {'claims': [statement.toJSON()]}  # add the statement on property: use []
    # to overwrite statement on property: do not use []
    response = repo.editEntity(identification, data, summary=summary)
    return response


def get_insee_code(administrative_division, insee_code):
    """

    :param administrative_division:
    :param insee_code:
    :return:
    """
    statements = administrative_division.claims
    if insee_code not in statements:
        return
    claims = statements[insee_code]
    for claim in claims:
        insee_code_value = claim.getTarget()
        # print(insee_code_value)
        # TODO: many values? get preferred rank?
        if claim.rank == 'preferred':
            return insee_code_value
    # if none is prefered, return last found value
    return insee_code_value


def check_duplicates(item, new_statement):
    """

    :param item:
    :param new_statement:
    :return:
    """
    item_statements = item.claims
    if new_statement.getID() in item_statements:
        for statement in item_statements[new_statement.getID()]:
            if statement.getTarget().amount == new_statement.getTarget().amount:
                # print('- duplicated:', item.getID(), ':', item.labels['fr'])
                if new_statement.qualifiers:
                    for pid in new_statement.qualifiers:
                        if pid in statement.qualifiers:
                            statement_qualifier_claim = statement.qualifiers[pid][0]
                            new_statement_qualifier_claim = new_statement.qualifiers[pid][0]
                            if statement_qualifier_claim.getTarget().year == new_statement_qualifier_claim.getTarget().year:
                                print('WARNING: duplicated:', item.getID(), ':', item.labels['fr'])
                                return True
            # elif statement.getRank() == 'preferred':
            #     print('- preferred', item.labels['fr'])
            #     statement.changeRank('normal')
    return False


def downgrade_ranks(item, new_statement, from_rank='preferred', to_rank='normal', summary=SUMMARY):
    """

    It assumes there is no duplicated.
    :param item:
    :param new_statement:
    :param from_rank:
    :param to_rank:
    :param summary:
    :return:
    """
    item_statements = item.claims
    if new_statement.getID() in item_statements:
        for statement in item_statements[new_statement.getID()]:
            # if statement.getTarget().amount == new_statement.getTarget().amount:
            #     print('- duplicated', item.labels['fr'])
            #     return True
            if statement.getRank() == from_rank:
                # print('- ' + from_rank, item.labels['fr'])
                print('WARNING: downgraded from rank', from_rank, ':', item.getID(), ':', item.labels['fr'])
                statement.changeRank(to_rank, summary=summary)

def check(query=None):  #, year=None, to=None, is_last=False):

    print(query)
    print()
    administrative_divisions = pg.WikidataSPARQLPageGenerator(query, site=SITE)
    for i, administrative_division in enumerate(administrative_divisions):
        administrative_division.get()
        print(i + 1, administrative_division.labels['fr'])


def main(query=None, summary=None, year=None, to=None, is_last=False, debug=DEBUG):
    """

    :param query:
    :param summary:
    :param year:
    :param to:
    :param is_last:
    :param debug:
    :return:
    """
    if year is None or to is None:
        return

    # Load data
    to_population_value = load_data(**PARAMS[to]) #(url=url, sheet_name=sheet_name, index=index, column=column)
    # print(to_population_value)

    # Create item generator
    administrative_divisions = pg.WikidataSPARQLPageGenerator(query, site=SITE)

    # Iterate over administrative divisions (items)
    insee_codes = []
    for i, administrative_division in enumerate(administrative_divisions):
        administrative_division.get()
        print(i + 1, administrative_division.labels['fr'])
        #statements = administrative_division.claims

        # Get insee_code
        insee_code = get_insee_code(administrative_division, PARAMS[to]['insee_code'])
        # Correct code for communes in Guadeloupe, Martinique, Guyane, La Réunion: remove repeated digit
        # if len(insee_code) == 6:
        #     insee_code = insee_code[:3] + insee_code[4:]

        insee_codes.append(insee_code)
        if insee_code not in to_population_value:
            # Wikidata entity wrongly stated as instance of this type of administrative division
            print('ERROR: to_population_value does not contain INSSE code:', insee_code, ':', administrative_division.getID(), ':', administrative_division.labels['fr'])
            continue

        # Create population claim
        population_value = to_population_value[insee_code]
        population_claim = create_claim(property=POPULATION, quantity=population_value)

        # Create qualifiers
        point_in_time = 'P585'
        date = {'year': int(year)}  # , 'month': 1, 'day': 1}
        point_in_time_claim = create_claim(property=point_in_time, **date)

        # Set qualifiers
        population_statement = set_qualifiers(population_claim, [point_in_time_claim])

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
        population_statement = set_sources(population_statement,
                                           [stated_in_claim, title_claim, publication_date_claim])

        # Set rank
        if is_last:
            population_statement.rank = 'preferred'

        # Check duplicated target value
        is_duplicated = check_duplicates(administrative_division, population_statement)
        if is_duplicated:
            continue

        if is_last and not debug:  # and not is_duplicated
            downgrade_ranks(administrative_division, population_statement, summary=summary)
        # if POPULATION in statements:
        #     for st in administrative_division.claims[POPULATION]:

        # Add statement
        #item = 'Q4115189'  # Wikidata Sandbox
        if not debug:
            add_statement(administrative_division, population_statement, summary=summary)

    print('ERROR: to_population_value - insee_codes:',
          set(to_population_value.keys()) - set(insee_codes))
    print('ERROR: insee_codes - to_population_values',
          set(insee_codes) - set(to_population_value.keys()))


def test_edit_item_2():

    # Create population claim
    population = 'P1082'
    # value = to_value[insee_code]
    value = 7
    population_claim = create_claim(property=population, quantity=value)

    # Create qualifiers
    point_in_time = 'P585'
    # TODO: from arg
    date = {'year': 2015}  #, 'month': 1, 'day': 1}
    point_in_time_claim = create_claim(property=point_in_time, **date)

    # Set qualifiers
    population_statement = set_qualifiers(population_claim, [point_in_time_claim])

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
    population_statement = set_sources(population_statement,
                            [stated_in_claim, title_claim, publication_date_claim])

    # Set rank
    population_statement.rank = 'preferred'

    # Add statement
    item = 'Q4115189'  # Wikidata Sandbox
    response = add_statement(item, population_statement)  #, summary=SUMMARY)



def test_edit_item_1():

    site = pywikibot.Site('wikidata', "wikidata")
    repo = site.data_repository()
    item = pywikibot.ItemPage(repo, 'Q4115189')  # Wikidata Sandbox

    # Crate claim
    population = 'P1082'  # pid: property_id
    claim = pywikibot.Claim(repo, population)  # , rank='preferred')
    # value = to_value[insee_code]
    value = 7
    quantity = pywikibot.WbQuantity(value, site=site)
    # print(type(quantity))
    claim.setTarget(quantity)
    # TODO: Remove if population is not the last one
    # claim.setRank('preferred')
    #item.addClaim(claim, summary="Add population 2015")
    # claim.changeRank('preferred')

    # Create qualifier
    point_in_time = 'P585'
    qualifier = pywikibot.Claim(repo, point_in_time)
    date = pywikibot.WbTime(year=2015, month=1, day=1)
    qualifier.setTarget(date)
    # claim.addQualifier(qualifier, summary=u'Adding a qualifier.')
    # set_qualifiers
    qualifier.isQualifier = True
    claim.qualifiers[qualifier.getID()] = [qualifier]

    # Create source
    stated_in = pywikibot.Claim(repo, 'P248')
    insee = pywikibot.ItemPage(repo, 'Q156616')
    stated_in.setTarget(insee)

    title = pywikibot.Claim(repo, 'P1476')
    text = pywikibot.WbMonolingualText("Recensement de la population 2015", 'fr')  # monolingual text
    title.setTarget(text)

    publication_date = pywikibot.Claim(repo, 'P577')
    date = pywikibot.WbTime(year=2017, month=12, day=27)
    publication_date.setTarget(date)

    # claim.addSources([statedin, publication_date], summary="Adding sources.")
    # claim.addSources([statedin], summary="Adding sources.")
    # claim.addSources([statedin, title, publication_date], summary="Adding sources.")

    # set_source
    claims = [stated_in, title, publication_date]
    source = defaultdict(list)
    for c in claims:
        c.isReference = True
        source[c.getID()].append(c)
    claim.sources.append(source)

    # Set rank
    # claim.changeRank('preferred', summary="Add population 2015")
    claim.rank = 'preferred'


    identification = {'id': item.getID()}
    data = {'claims': [claim.toJSON()]}  # add the statement on property: use []
                                        # to overwrite statement on property: do not use []
    response = repo.editEntity(identification, data, summary="Add 2015 population")

def test():

    # site = pywikibot.Site('test', "wikidata")
    site = SITE  # pywikibot.Site('wikidata', "wikidata")
    repo = REPO  # site.data_repository()
    # item = pywikibot.ItemPage(repo, "Q121006")  # test:
    item = pywikibot.ItemPage(repo, 'Q4115189')  # Wikidata Sandbox

    # Add claim
    prop = 'P1082'
    claim = pywikibot.Claim(repo, prop)  # , rank='preferred')
    #value = to_value[insee_code]
    value = 666
    quantity = pywikibot.WbQuantity(value, site=site)
    #print(type(quantity))
    claim.setTarget(quantity)
    # TODO: Remove if population is not the last one
    # claim.setRank('preferred')
    item.addClaim(claim, summary="Add population 2015")
    #claim.changeRank('preferred')

    # Create qualifier
    point_in_time = 'P585'
    qualifier = pywikibot.Claim(repo, point_in_time)
    date = pywikibot.WbTime(year=2015)  # , month=3, day=20)
    qualifier.setTarget(date)
    #claim.addQualifier(qualifier, summary=u'Adding a qualifier.')
    # set_qualifier
    qualifier.isQualifier = True
    claim.qualifiers[qualifier.getID()] = [qualifier]


    # Create source
    statedin = pywikibot.Claim(repo, 'P248')
    insee = pywikibot.ItemPage(repo, 'Q156616')
    statedin.setTarget(insee)

    title = pywikibot.Claim(repo, 'P1476')
    text = pywikibot.WbMonolingualText("Recensement de la population 2015", 'fr')  # monolingual text
    title.setTarget(text)

    publication_date = pywikibot.Claim(repo, 'P577')
    date = pywikibot.WbTime(year=2017, month=12, day=27)
    publication_date.setTarget(date)

    # claim.addSources([statedin, publication_date], summary="Adding sources.")
    # claim.addSources([statedin], summary="Adding sources.")
    #claim.addSources([statedin, title, publication_date], summary="Adding sources.")

    # set_source
    claims = [statedin, title, publication_date]
    source = defaultdict(list)
    for c in claims:
        c.isReference = True
        source[c.getID()].append(c)
    claim.sources.append(source)

    # Set rank
    #claim.changeRank('preferred', summary="Add population 2015")
    claim.rank = 'preferred'

    claim.repo.save_claim(claim, summary="Add population 2015")



if __name__ == '__main__':
    """
    
    python ./scripts/add_population_0.py -y 2015 -t arrondissements -l --check | tee logs/check_add_population_2015_arrondissements.log
    python ./scripts/add_population_0.py -y 2015 -t arrondissements -l --debug | tee logs/debug_add_population_2015_arrondissements.log
    python ./scripts/add_population_0.py -y 2015 -t arrondissements -l | tee logs/add_population_2015_arrondissements.log

    
    python ./scripts/add_population_0.py -y 2015 -t cantons -l --check | tee logs/check_add_population_2015_cantons.log
    python ./scripts/add_population_0.py -y 2015 -t cantons -l --debug | tee logs/debug_add_population_2015_cantons.log
    python ./scripts/add_population_0.py -y 2015 -t cantons -l | tee logs/add_population_2015_cantons.log


    python ./scripts/add_population_0.py -y 2015 -t communes -l --check | tee logs/check_add_population_2015_communes.log
    python ./scripts/add_population_0.py -y 2015 -t communes -l --debug | tee logs/debug_add_population_2015_communes.log
    python ./scripts/add_population_0.py -y 2015 -t communes -l | tee logs/add_population_2015_communes.log
    

    """
    # Parse arguments
    args = parse_args()
    print(args.to)

    if args.check:
        # Set check variables
        check_query = (CHECK_QUERY
            .replace('{administrative_division}', PARAMS[args.to]['administrative_division'])
            .replace('{year}', args.year)
        )
        check(check_query)

    else:
        # Set variables
        # query = (QUERY
        #     .replace('{administrative_division}', PARAMS[args.to]['administrative_division'])
        #     .replace('{year}', args.year)
        # )

        query = (CUSTOM_QUERY_ADDED_INSEE_CODE
            .replace('{administrative_division}', PARAMS[args.to]['administrative_division'])
            .replace('{insee_code}', PARAMS[args.to]['insee_code'])
        )
        if args.to == 'communes' or args.to == 'communes_ass_del':
            query = CORRECTED_QUERY_FOR_COMMUNES
        elif args.to == 'coms':
            query = (CUSTOM_QUERY_FOR_COMS
                .replace('{insee_code}', PARAMS[args.to]['insee_code'])
            )

        summary = SUMMARY.replace('2015', args.year)#.format(args.year)
        print(query)
        print(summary)

        population_statement = main(query=query, summary=summary,
                                year=args.year, to=args.to, is_last=args.is_last, debug=args.debug)


