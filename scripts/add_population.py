"""Add population."""

import argparse
import logging
from pathlib import Path

import pandas as pd

import pywikibot
from pywikibot import pagegenerators as pg
import wikidatabot
from wikidatabot.models import Claim, Statement, Item


logger = logging.getLogger('add_population')


PATH_FRANCE_2017 = Path('D:/data/insee/populations/2017/ensemble.xls')

# Constants
INSTANCE_OF = 'P31'
SUBCLASS = 'P279'
START_TIME = 'P580'
END_TIME = 'P582'
LOCATED_IN = 'P131'  # located in the administrative territorial entity
DEBUG = True
POPULATION = 'P1082'
POINT_IN_TIME = 'P585'
STATED_IN = 'P248'
INSEE = 'Q156616'
TITLE = 'P1476'
PUBLICATION_DATE = 'P577'
DETERMINATION_METHOD = 'P459'
CENSUS = 'Q39825'

PARAMS = {
    '2014': {
        'nouvelle_caledonie': {
            'cog_year': '2017',
            'location': 'Q33788',  # Nouvelle-Calédonie
            'summary': "Add New Caledonia 2014 population",
            'source_title': "Recensement de la population effectué en Nouvelle-Calédonie en 2014",
            'source_language': 'fr',
            'publication_date': {'year': 2015, 'month': 2, 'day': 1},
            'communes': {
                'path': '~/share/data/insee/populations/nouvelle_caledonie/2014/populations_nouvelle_caledonie_2014_communes.csv',
                'administrative_division': 'Q484170',  # commune of France
                'insee_code': 'P374',  # INSEE municipality code
                'sheet_name': None,
                'index': ['Code COM', 'Code commune'],
                'column': 'Population municipale',
            },
        },
    },
    '2017': {
        'mayotte': {
            'cog_year': '2017',
            'location': 'Q17063',  # Mayotte
            'summary': "Add Mayotte 2017 population",
            'source_title': "Recensement de la population 2017 de Mayotte",
            'source_language': 'fr',
            'publication_date': {'year': 2017, 'month': 12, 'day': 27},
            'cantons':{
                'path': '~/share/data/insee/populations/mayotte/2017/populations_mayotte_2017_cantons.csv',
                'administrative_division': 'Q18524218',  # canton of France (starting March 2015)
                'insee_code': 'P2506',  # INSEE canton code
                'sheet_name': None,
                'index': ['Code département', 'Code canton'],
                'column': 'Population municipale',
            },
            'communes':{
                'path': '~/share/data/insee/populations/mayotte/2017/populations_mayotte_2017_communes.csv',
                'administrative_division': 'Q484170',  # commune of France
                'insee_code': 'P374',  # INSEE municipality code
                'sheet_name': None,
                'index': ['Code département', 'Code commune'],
                'column': 'Population municipale',
            },
        },
        'polynesie': {
            'cog_year': '2017',
            'location': 'Q30971',  # Polynésie française
            'summary': "Add French Polynesia 2017 population",
            'source_title': "Recensement de la population 2017 de Polynésie française",
            'source_language': 'fr',
            'publication_date': {'year': 2017, 'month': 12, 'day': 27},
            'communes': {
                'path': '~/share/data/insee/populations/polynesie/2017/populations_polynesie_2017_communes.csv',
                'administrative_division': 'Q484170',  # commune of France
                'insee_code': 'P374',  # INSEE municipality code
                'sheet_name': None,
                'index': ['Code COM', 'Code commune'],
                'column': 'Population municipale',
            },
        },
        'france': {
            'cog_year': '2019',
            'location': {'MINUS': ['Q17063', 'Q30971']},  # MINUS: [Mayotte, French Polynesia]
            # None,  # 'Q142',  # France <- this gives TimeOut
            'summary': "Add France 2017 population",
            'population_date': {'year': 2017, 'month': 1, 'day': 1},
            'stated_in': 'Q81204110',  # Populations légales 2017
            # 'source_title': "Populations légales 2017",
            # 'source_language': 'fr',
            # 'publication_date': {'year': 2019, 'month': 12, 'day': 30},
            'regions': {
                'path': PATH_FRANCE_2017,
                'administrative_division': 'Q36784',  # region of France
                'insee_code': 'P2585',  # INSEE region code
                'sheet_name': 'Régions',
                'index': 'Code région',
                'column': 'Population municipale',
            },
            'departements': {
                'path': PATH_FRANCE_2017,
                'administrative_division': 'Q6465',  # department of France
                'insee_code': 'P2586',  # INSEE department code
                'sheet_name': 'Départements',
                'index': 'Code département',
                'column': 'Population municipale',
            },
            # 'droms': They are already included in regions
            'arrondissements': {
                'path': PATH_FRANCE_2017,
                'administrative_division': 'Q194203',  # arrondissement of France
                'insee_code': 'P3423',  # INSEE arrondissement code
                'sheet_name': 'Arrondissements',
                'index': ['Code département', 'Code arrondissement'],
                'column': 'Population municipale',
            },
            'cantons': {
                'path': PATH_FRANCE_2017,
                'administrative_division': 'Q18524218',  # canton of France (starting March 2015)
                'insee_code': 'P2506',  # INSEE canton code
                'sheet_name': 'Cantons et métropoles',
                'index': ['Code département', 'Code canton'],
                'column': 'Population municipale',
            },
            'communes': {
                'path': PATH_FRANCE_2017,
                'administrative_division': ['Q484170', 'Q2989454'],  # [commune of France, commune nouvelle]
                'insee_code': 'P374',  # INSEE municipality code
                'sheet_name': 'Communes',
                'index': ['Code département', 'Code commune'],
                'column': 'Population municipale',
            },
        },

    },
}

QUERY = """
SELECT DISTINCT ?item WHERE {
  {values}

  ?item p:{instance_of} ?st .
  ?st ps:{instance_of} wd:{administrative_division} .
  
  OPTIONAL{?st pq:{start_time} ?start_time_date}
  FILTER(IF(BOUND(?start_time_date), ?start_time_date <= "{cog_year}-01-01"^^xsd:dateTime, true))
  
  OPTIONAL{?st pq:{end_time} ?end_time_date}
  FILTER(IF(BOUND(?end_time_date), ?end_time_date > "{cog_year}-01-01"^^xsd:dateTime, true))
  
  {located_in_location}
}
 """\
    .replace('{instance_of}', INSTANCE_OF)\
    .replace('{start_time}', START_TIME)\
    .replace('{end_time}', END_TIME)


def config_logger(log_filename=''):
    # Set logging level
    logger.setLevel(logging.DEBUG)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)8s] %(message)s')
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if log_filename:
        # Create file handler
        fh = logging.FileHandler(filename=log_filename)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def parse_args():
    parser = argparse.ArgumentParser(description="Add population")
    parser.add_argument('-y', '--year', required=True)
    parser.add_argument('-a', '--at', default='mayotte')
    parser.add_argument('-t', '--to', default='regions')
    parser.add_argument('-l', '--is-last', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--log', default='')

    args = parser.parse_args()
    return args


def load_data(path=None, sheet_name=None, index=None, column=None, **kwargs):
    path = Path(path)
    if '~' in str(path):
        path = path.expanduser()
    if isinstance(index, str):
        to_dtype = {index: str}
    else:
        to_dtype = {idx: str for idx in index}
    # Read
    if path.suffix.endswith('xls'):
        df = pd.read_excel(path, sheet_name=sheet_name, header=7, dtype=to_dtype)
    elif path.suffix.endswith('csv'):
        df = pd.read_csv(path, sep='\t', dtype=to_dtype)
    # Set index
    if isinstance(index, str):
        df = df.set_index(index)
    else:
        df['code'] = df[index[0]]
        for idx in index[1:]:
            df['code'] += df[idx]
        # Correct code for communes in Guadeloupe, Martinique, Guyane, La Réunion: remove repeated digit
        df['code'] = df['code'].where(df['code'].str.len() < 6, df['code'].str[:3] + df['code'].str[4:])
        df = df.set_index('code')
    # To dict
    to_value = df[column].to_dict()
    return to_value


def get_insee_code(administrative_division, insee_code):
    """
    Get INSEE code value from the administrative division item.

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
            # TODO: warn if new statement has different amount but the same year (see Paris)
            if statement.getTarget().amount == new_statement.getTarget().amount:
                # print('- duplicated:', item.getID(), ':', item.labels['fr'])
                if new_statement.qualifiers:
                    for pid in new_statement.qualifiers:
                        if pid in statement.qualifiers:
                            statement_qualifier_claim = statement.qualifiers[pid][0]
                            new_statement_qualifier_claim = new_statement.qualifiers[pid][0]
                            if statement_qualifier_claim.getTarget().year == new_statement_qualifier_claim.getTarget().year:
                                logger.warning(f"Duplicated claim: item {item.labels.get('fr')} ({item.getID()}) "
                                               f"already contains the same population claim")
                                return True
            # elif statement.getRank() == 'preferred':
            #     print('- preferred', item.labels['fr'])
            #     statement.changeRank('normal')
    return False


def downgrade_ranks(item, new_statement, from_rank='preferred', to_rank='normal', summary=None):
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
                logger.info(f"Downgrade rank: from rank {from_rank} in item {item.labels.get('fr')} ({item.getID()})")
                statement.changeRank(to_rank, summary=summary)


def main(query=None, summary=None, population_date=None, stated_in=None,
         source_title=None, source_language=None, publication_date=None,
         year=None, at=None, to=None, is_last=False, debug=DEBUG, params=None):

    if year is None or to is None:
        return

    # Load data
    to_population_value = load_data(**params)

    # Create item generator
    administrative_divisions = pg.WikidataSPARQLPageGenerator(query, site=wikidatabot.site)

    # Iterate over administrative divisions (items)
    for i, administrative_division in enumerate(administrative_divisions):
        administrative_division.get()
        administrative_division_label = administrative_division.labels.get('fr')
        if not administrative_division_label:
            logger.warning(f"No fr label: item {administrative_division.getID()}")
            administrative_division_label = administrative_division.getID()
        # logger.info(f"Item {i + 1}: {administrative_division_label} ({administrative_division.getID()})")

        # Get insee_code from item
        insee_code = get_insee_code(administrative_division, params['insee_code'])

        # Check if insee code value is in INSEE population file
        if insee_code not in to_population_value:
            # Wikidata entity wrongly stated as instance of this type of administrative division
            logger.error(f"Missing INSEE code: population file does not contain INSSE code {insee_code}, which is "
                         f"present in item {administrative_division_label} ({administrative_division.getID()})")
            continue
        else:
            # logger.info(f"Found INSEE code: population file contains INSEE code {insee_code}, which is present in "
            #             f"item {administrative_division_label} ({administrative_division.getID()})")
            logger.info(f"Item: {administrative_division_label} ({administrative_division.getID()}) with INSEE code {insee_code}")

        # Create population claim
        population_value = to_population_value.pop(insee_code)
        population_claim = Claim(property=POPULATION, quantity=population_value)

        # Create qualifiers
        if not population_date:
            population_date = {'year': int(year)}  # , 'month': 1, 'day': 1}
        point_in_time_claim = Claim(property=POINT_IN_TIME, **population_date)
        determination_method_claim = Claim(property=DETERMINATION_METHOD, item=CENSUS)
        qualifiers = [point_in_time_claim, determination_method_claim]

        # Create sources
        if stated_in:
            stated_in_claim = Claim(property=STATED_IN, item=stated_in)
            sources = [stated_in_claim]
        else:
            stated_in_claim = Claim(property=STATED_IN, item=INSEE)
            title_claim = Claim(property=TITLE, text=source_title, language=source_language)
            publication_date_claim = Claim(property=PUBLICATION_DATE, **publication_date)
            sources = [stated_in_claim, title_claim, publication_date_claim]

        # Create population statement
        rank = 'preferred' if is_last else 'normal'
        population_statement = Statement(claim=population_claim,
                                         rank=rank,
                                         qualifiers=qualifiers,
                                         sources=sources)

        # Check duplicated target value
        is_duplicated = check_duplicates(administrative_division, population_statement._statement)
        if is_duplicated:
            continue

        # Downgrade rank of the other analogue statements
        if is_last and not debug:  # and not is_duplicated
            downgrade_ranks(administrative_division, population_statement._statement, summary=summary)

        # Add statement
        if not debug:
            # pass
            # add_statement(administrative_division, insee_code_statement, summary=summary)
            administrative_division_item = Item.from_pwb(administrative_division)
            administrative_division_item.add_statement(population_statement, summary=summary)
        else:
            # print(population_statement._statement, summary)
            if i >= 20:
                break

    if to_population_value:
        logger.error(f"Unused INSEE codes: population file contains unused INSEE codes "
                     f"{list(to_population_value.keys())}")


if __name__ == '__main__':
    """
    python ./scripts/add_population.py -y 2017 -a france -t communes -l --debug --log logs/test.log


    python ./scripts/add_population.py -y 2017 -a france -t regions -l --debug
    python ./scripts/add_population.py -y 2017 -a france -t regions -l | tee logs/add_population_2017_france_regions.log

    python ./scripts/add_population.py -y 2017 -a france -t departements -l --debug
    python ./scripts/add_population.py -y 2017 -a france -t departements -l | tee logs/add_population_2017_france_departements.log

    python ./scripts/add_population.py -y 2017 -a france -t arrondissements -l --debug
    python ./scripts/add_population.py -y 2017 -a france -t arrondissements -l | tee logs/add_population_2017_france_arrondissements.log

    python ./scripts/add_population.py -y 2017 -a france -t cantons -l --debug
    python ./scripts/add_population.py -y 2017 -a france -t cantons -l | tee logs/add_population_2017_france_cantons.log

    python ./scripts/add_population.py -y 2017 -a france -t communes -l --debug
    python ./scripts/add_population.py -y 2017 -a france -t communes -l | tee logs/add_population_2017_france_communes.log
    python ./scripts/add_population.py -y 2017 -a france -t communes -l --log logs/add_population_2017_france_communes.log


    python ./scripts/add_population.py -y 2017 -a mayotte -t cantons -l --debug
    python ./scripts/add_population.py -y 2017 -a mayotte -t cantons -l | tee logs/add_population_2017_mayotte_cantons.log
    
    python ./scripts/add_population.py -y 2017 -a mayotte -t communes -l --debug
    python ./scripts/add_population.py -y 2017 -a mayotte -t communes -l | tee logs/add_population_2017_mayotte_communes.log

    python ./scripts/add_population.py -y 2017 -a polynesie -t communes -l | tee logs/add_population_2017_polynesie_communes.log
    
    ./scripts/add_population.py -y 2014 -a nouvelle_caledonie -t communes -l | tee logs/add_population_2014_nouvelle_caledonie_communes.log
    
    

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
    logger.info(args.to)

    # if args.check:
    #     # Set check variables
    #     check_query = (CHECK_QUERY
    #         .replace('{administrative_division}', PARAMS[args.to]['administrative_division'])
    #         .replace('{year}', args.year)
    #         )
    #     check(check_query)
    #
    # else:

    # Configurate logger
    config_logger(log_filename=args.log)
    logger.info(f"START add_population")

    # Set variables
    administrative_division = PARAMS[args.year][args.at][args.to]['administrative_division']
    if isinstance(administrative_division, str):
        query = QUERY \
            .replace('{values}', '') \
            .replace('{administrative_division}', administrative_division)\
            .replace('{cog_year}', PARAMS[args.year][args.at]['cog_year'])
    else:
        administrative_division = ' '.join(f"wd:{q_code}" for q_code in administrative_division)
        values = "VALUES ?administrative_division { " + administrative_division + " }"
        query = QUERY \
            .replace('{values}', values) \
            .replace('wd:{administrative_division}', '?administrative_division') \
            .replace('{cog_year}', PARAMS[args.year][args.at]['cog_year'])

    location = PARAMS[args.year][args.at]['location']
    if location:
        if 'MINUS' in location:
            locations = location['MINUS']
            located_in_location = ['']
            for location in locations:
                located_in_location.append('  MINUS {?item wdt:{located_in} wd:{location}}'
                                           .replace('{located_in}', LOCATED_IN).replace('{location}', location))
            query = query.replace('{located_in_location}', '\n'.join(located_in_location))
        else:
            query = query.replace('{located_in_location}', '?item wdt:{located_in}+ wd:{location} .  # Recursive')\
                .replace('{located_in}', LOCATED_IN)\
                .replace('{location}', location)
    else:
        query = query.replace('{located_in_location}', '')

    # query = (CUSTOM_QUERY_ADDED_INSEE_CODE
    #     .replace('{administrative_division}', PARAMS[args.to]['administrative_division'])
    #     .replace('{insee_code}', PARAMS[args.to]['insee_code'])
    #     )

    # if args.to == 'communes' or args.to == 'communes_ass_del':
    #     query = CORRECTED_QUERY_FOR_COMMUNES
    # elif args.to == 'coms':
    #     query = (CUSTOM_QUERY_FOR_COMS
    #         .replace('{insee_code}', PARAMS[args.to]['insee_code'])
    #         )

    summary = PARAMS[args.year][args.at]['summary']
    population_date = PARAMS[args.year][args.at].get('population_date')
    stated_in = PARAMS[args.year][args.at].get('stated_in')
    # Legacy:
    source_title = PARAMS[args.year][args.at].get('source_title')
    source_language = PARAMS[args.year][args.at].get('source_language')
    publication_date = PARAMS[args.year][args.at].get('publication_date')

    params = PARAMS[args.year][args.at][args.to]
    logger.info(f"SPARQL query: {query}")
    logger.info(f"Summary: {summary}")
    # logger.info(args.is_last)

    main(query=query,
         year=args.year, at=args.at, to=args.to,
         is_last=args.is_last, debug=args.debug,
         summary=summary,
         population_date=population_date, stated_in=stated_in,
         source_title=source_title, source_language=source_language, publication_date=publication_date,
         params=params
         )
    logger.info(f"END add_population")
