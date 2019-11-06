"""


"""


import argparse
from collections import defaultdict
import os
import pandas as pd
import pywikibot
from pywikibot import pagegenerators as pg
import re

from wikidatabot.types import SITE, Claim, Statement, Item


INSTANCE_OF = 'P31'
SUBCLASS = 'P279'
LOCATED_IN = 'P131'  # located in the administrative territorial entity

QUERY = ("""
    SELECT ?item WHERE {
        # ?item wdt:{instance_of}/wdt:{subclass}* wd:{administrative_division}.
        ?item p:{instance_of} ?st .
        ?st ps:{instance_of} wd:{administrative_division} .
        # ?st ps:{instance_of} ?instance_of .
        # VALUES ?instance_of {wd:Q666943 wd:Q21869758} .
        
        OPTIONAL{?st pq:P580 ?start_time_date .}
        FILTER(IF(BOUND(?start_time_date), ?start_time_date <= "2017-01-01"^^xsd:dateTime, true)) .
  
        OPTIONAL{?st pq:P582 ?end_time_date .}
        FILTER(IF(BOUND(?end_time_date), ?end_time_date > "2017-01-01"^^xsd:dateTime, true)) .
        
        # "unknown value" insee_code
        ?item wdt:{insee_code} ?insee_code .
        FILTER isBLANK(?insee_code) .
        
        ?item wdt:{located_in} wd:{location} .
        
        # FILTER NOT EXISTS {
        #     ?item wdt:{insee_code} ?insee_code
        # }
        
    }
 """.replace('{instance_of}', INSTANCE_OF)
    .replace('{subclass}', SUBCLASS)
    .replace('{located_in}', LOCATED_IN)
)

SUMMARY = "Add INSEE code as of 2017-01-01"

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
        'column': "Nom de l'arrondissement",
        'regex': re.compile(r"arrondissement \w+\W(.+)$"),
    },
    'cantons': {
        'administrative_division': 'Q18524218',  # canton of France (starting March 2015)
        'insee_code': 'P2506',  # INSEE canton code
        'sheet_name': 'Cantons et métropoles',
        'index': ['Code département', 'Code canton'],
        'column': 'Nom du canton',
        'regex': re.compile(r"canton \w+\W(.+)$"),
    },
    'communes': {
        'administrative_division': 'Q484170',  #  commune of France;  commune nouvelle
        'insee_code': 'P374',  # INSEE municipality code
        'sheet_name': 'Communes',
        'index': ['Code département', 'Code commune'],
        'column': 'Nom de la commune',
        'regex': '',
    },
    'communes_ass_del': {
        'administrative_division': 'Q',  # commune of France
        'insee_code': 'P374',  # INSEE municipality code
        'sheet_name': 'Communes associées ou déléguées',
        'index': ['Code département', 'Code commune'],
        'column': 'Nom de la commune',
        'regex': '',
    },
}


# SITE = pywikibot.Site('wikidata', "wikidata")

# To load data
URL = 'https://www.insee.fr/fr/statistiques/fichier/3292622/ensemble.xls'
URL = '~/share/data/insee/ensemble.xls'
URL = os.path.expanduser(URL)
SHEET_NAME = 'Régions'
INDEX = 'Code région'
COLUMN = 'Population municipale'


def load_data(path=None, sheet_name=SHEET_NAME, index=INDEX, column=COLUMN, **kwargs):
    if not path:
        path = URL
    path = os.path.expanduser(path)
    if isinstance(index, str):
        to_dtype = {index: str}
    else:
        to_dtype = {idx: str for idx in index}
    if path.endswith('xls'):
        df = pd.read_excel(path, sheet_name=sheet_name, header=7, dtype=to_dtype)
    elif path.endswith('csv'):
        df = pd.read_csv(path, sep='\t', dtype=to_dtype)
    if isinstance(index, str):
        df = df.set_index(index)
    else:
        df['code'] = df[index[0]]
        for idx in index[1:]:
            df['code'] += df[idx]
    #     df = df.set_index('code')
    # to_value = df[column].to_dict()
    # TODO: Use also department name
    # print(column)
    # print(df.columns)

    if df[column].duplicated().any():
        duplicated = df[column][df[column].duplicated()].values
        print("Duplicated names:", len(duplicated), ':', duplicated)
        df = df.drop_duplicates(subset=column, keep=False)
    df = df.set_index(column)
    to_value = df['code'].to_dict()
    return to_value


def parse_args():
    parser = argparse.ArgumentParser(description="Add population")
    # parser.add_argument('-y', '--year', required=True)
    parser.add_argument('-a', '--at')
    parser.add_argument('-t', '--to', default='regions')
    parser.add_argument('-l', '--is-last', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--check', action='store_true')

    args = parser.parse_args()
    return args


def check_duplicates(item, new_statement):
    """

    :param item:
    :param new_statement:
    :return:
    """
    item_statements = item.claims
    if new_statement.getID() in item_statements:
        for statement in item_statements[new_statement.getID()]:
            # if statement.getTarget().amount == new_statement.getTarget().amount:
            # For a string
            if statement.getTarget() == new_statement.getTarget():
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


def main(query=None, summary=None, year=None, to=None, is_last=False, debug=True, path=None, params=None):

    # Load data
    to_insee_code_value = load_data(path=path, **params)  #(url=url, sheet_name=sheet_name, index=index, column=column)
    # print(to_insee_code_value)

    # Create item generator
    administrative_divisions = pg.WikidataSPARQLPageGenerator(query, site=SITE)
    # print('After Page Generator')

    # Iterate over administrative divisions (items)
    count = 0
    for i, administrative_division in enumerate(administrative_divisions):
        administrative_division.get()
        lang = 'fr'  # 'fr'
        administrative_division_name = administrative_division.labels[lang]
        # print(i + 1, administrative_division.labels[lang])
        regex = params['regex']
        if regex:
            match = regex.match(administrative_division_name)
            if match:
                name = match.group(1)
        else:
            name = administrative_division_name
        if name in to_insee_code_value:
            count += 1
            insee_code_value = to_insee_code_value[name]
            print(count, ':', administrative_division.getID(), ':', insee_code_value, ':', administrative_division_name)

            # Create insee_code claim
            insee_code = params['insee_code']
            # insee_code_claim = create_claim(property=insee_code, value=insee_code_value)
            insee_code_claim = Claim(property=insee_code, value=insee_code_value)

            # TODO
            if True:  # REPLACE: for None insee code**************************************************************
                # insee_code_claim = Claim(property=insee_code, value=insee_code_value)
                insee_code_claim._claim.snak = administrative_division.claims[insee_code][0].snak

            # if debug:
            #     print(insee_code_claim._claim.toJSON())

            # Create qualifiers
            point_in_time = 'P585'
            # TODO: from arg
            date = {'year': 2017, 'month': 1, 'day': 1}  # , 'month': 1, 'day': 1}
            # point_in_time_claim = create_claim(property=point_in_time, **date)
            point_in_time_claim = Claim(property=point_in_time, **date)

            # TODO
            # Set qualifiers
            # population_statement = set_qualifiers(population_claim, [point_in_time_claim])

            # Create sources
            stated_in = 'P248'
            insee = 'Q156616'
            # stated_in_claim = create_claim(property=stated_in, item=insee)
            stated_in_claim = Claim(property=stated_in, item=insee)

            title = 'P1476'
            text = "Code officiel géographique au 1er janvier 2017"
            language = 'fr'
            # title_claim = create_claim(property=title, text=text, language=language)
            title_claim = Claim(property=title, text=text, language=language)

            publication_date = 'P577'
            date = {'year': 2017, 'month': 9, 'day': 22}
            # publication_date_claim = create_claim(property=publication_date, **date)
            publication_date_claim = Claim(property=publication_date, **date)

            # TODO
            # Set sources
            # population_statement = set_sources(population_statement,
            #                                    [stated_in_claim, title_claim, publication_date_claim])

            # Create insee_code statement
            insee_code_statement = Statement(claim=insee_code_claim,
                                             rank='normal',
                                             qualifiers=[point_in_time_claim],
                                             sources=[stated_in_claim, title_claim, publication_date_claim])
            # if debug:
            #     print(insee_code_statement._statement.toJSON())

            # Check duplicated target value
            is_duplicated = check_duplicates(administrative_division, insee_code_statement._statement)
            if is_duplicated:
                continue

            if not debug:
                # pass
                # add_statement(administrative_division, insee_code_statement, summary=summary)
                administrative_division_item = Item(administrative_division)
                administrative_division_item.add_statement(insee_code_statement, summary=summary)

            # break




if __name__ == '__main__':
    # Parse arguments
    args = parse_args()
    print(args.to)

    path = None
    location = 'None'
    params = PARAMS[args.to]
    if args.at == 'mayotte':
        path = '~/share/data/insee/populations/mayotte/2017/populations_mayotte_2017_cantons.csv'
        location = 'Q17063'  # Mayotte
    elif args.at == 'polynesie':
        path = '~/share/data/insee/populations/polynesie/2017/populations_polynesie_2017_communes.csv'
        location = 'Q30971'  # Polynésie française
        params['index'] = ['Code COM', 'Code commune']
    else:
        pass


    # Set variables
    query = (QUERY
        .replace('{administrative_division}', params['administrative_division'])
        .replace('{insee_code}', params['insee_code'])
        .replace('{location}', location)
    )
    query = re.sub(r'.*wd:None.*', '', query)
    summary = SUMMARY#.replace('2017', args.year)  # .format(args.year)
    print(query)
    print(summary)

    main(query=query, summary=summary, path=path,  # year=args.year,
         to=args.to, is_last=args.is_last, debug=args.debug,
         params=params)
