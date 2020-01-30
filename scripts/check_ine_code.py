"""

python ./scripts/check_ine_code.py -y 2019 --debug

python ./scripts/check_ine_code.py -y 2019 --log logs/check_ine_code-0.log
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

from pywikibot import pagegenerators as pg
import wikidatabot
from wikidatabot.models import Claim, Statement, Item


logger = logging.getLogger("check_ine_code")

PATH_CODES_2019 = Path('D:/data/ine/codigos/2019/19codmun.xlsx')

# Constants
INSTANCE_OF = 'P31'
SUBCLASS_OF = 'P279'
START_TIME = 'P580'
END_TIME = 'P582'
OFFICIAL_NAME = 'P1448'

INE_MUNICIPALITY_CODE = 'P772'
MUNICIPALITY_OF_SPAIN = 'Q2074737'
MUNICIPALITY_OF_ARAGON = 'Q61763947'
MUNICIPALITY_OF_ASTURIAS = 'Q5055981'
MUNICIPALITY_OF_CATALONIA = 'Q33146843'
MUNICIPALITY_OF_GALICIA = 'Q2276925'

QUERY = """
SELECT DISTINCT ?item WHERE {

  {values}

  ?item p:{instance_of} ?st .
  ?st ps:{instance_of} wd:{administrative_division} .
  # ?st ps:{instance_of}/wdt:{subclass_of}? wd:{administrative_division} .  # this takes 13 min instead of 3
                                                                            # also former_municipality_of_Spain is subclass

  OPTIONAL{?st pq:{start_time} ?start_time_date}
  FILTER(IF(BOUND(?start_time_date), ?start_time_date <= "{year}-01-01"^^xsd:dateTime, true))

  OPTIONAL{?st pq:{end_time} ?end_time_date}
  FILTER(IF(BOUND(?end_time_date), ?end_time_date > "{year}-01-01"^^xsd:dateTime, true))

}
 """ \
    .replace('{instance_of}', INSTANCE_OF) \
    .replace('{subclass_of}', SUBCLASS_OF) \
    .replace('{start_time}', START_TIME) \
    .replace('{end_time}', END_TIME)

PARAMS = {
    '2019': {
        'path': PATH_CODES_2019,
        'administrative_division': [MUNICIPALITY_OF_SPAIN, MUNICIPALITY_OF_ARAGON, MUNICIPALITY_OF_ASTURIAS,
                                    MUNICIPALITY_OF_CATALONIA, MUNICIPALITY_OF_GALICIA],
    },
}


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
    parser = argparse.ArgumentParser(description="Check ine code")
    parser.add_argument('-t', '--to', default=MUNICIPALITY_OF_SPAIN)
    parser.add_argument('-y', '--year', required=True)
    parser.add_argument('--log', default='')
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args()


def load_data(path=''):
    path = Path(path)
    index = ('CPRO', 'CMUN')
    to_dtype = {idx: str for idx in index}
    # if path.suffix.endswith('xls') or path.suffix.endswith('xlsx'):
    df = pd.read_excel(path, sheet_name=0, header=1, dtype=to_dtype)
    # Strip column names
    df.columns = [col.strip() for col in df.columns]
    df['code'] = df[index[0]]
    for idx in index[1:]:
        df['code'] += df[idx]
    # Index
    if df['code'].duplicated().any():
        duplicated = df['code'][df['code'].duplicated()].values
        logger.error(f"Duplicated codes: dropped {len(duplicated)} duplicates: {duplicated}")
    df = df.set_index('code')
    # To dict
    column = 'NOMBRE'
    to_value = df[column].to_dict()
    # if df[column].duplicated().any():
    #     duplicated = df[column][df[column].duplicated()].values
    #     logger.error(f"Duplicated names: dropped {len(duplicated)} duplicates: {duplicated}")
    #     df = df.drop_duplicates(subset=column, keep=False)
    #     # dropped 17 duplicates: ['Cabanes' 'Sobrado' 'Arroyomolinos',...
    # # To dict
    # df = df.set_index(column)
    # to_value = df['code'].to_dict()
    return to_value


def get_ine_code(item, ine_code):
    statements = item.statements
    if ine_code not in statements:
        return
    claims = statements[ine_code]
    if len(claims) > 1:
        logger.warning(f"Multiple INE codes for item {item.id}")
    for claim in claims:
        ine_code_value = claim.getTarget()
        # print(insee_code_value)
        # TODO: many values? get preferred rank?
        if claim.rank == 'preferred':
            return ine_code_value
    # if none is prefered, return last found value
    if len(claims) > 1:
        logger.warning(f"No preferred rank among multiple INE codes for item {item.id}")
    return ine_code_value


if __name__ == '__main__':

    # Parse arguments
    args = parse_args()
    params = PARAMS[args.year]
    administrative_division = params['administrative_division']

    # Configurate logger
    config_logger(log_filename=args.log)
    logger.info('START check_ine_code')

    # Load data
    to_ine_code_value = load_data(path=params['path'])  # **params)

    # Query
    query = QUERY.replace('{year}', args.year)
    if isinstance(administrative_division, str):
        values = ''
        query = query.replace('{administrative_division}', administrative_division)
    else:
        administrative_division = ' '.join(f"wd:{q_code}" for q_code in administrative_division)
        values = "VALUES ?administrative_division { " + administrative_division + " }"
        query = query.replace('wd:{administrative_division}', '?administrative_division')
    query = query.replace('{values}', values)

    # Create item generator
    pwb_items = pg.WikidataSPARQLPageGenerator(query, site=wikidatabot.site)

    # Iterate over administrative divisions (items)
    used_ine_codes = {}
    for i, pwb_item in enumerate(pwb_items):
        # pwb_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, 'Q764858')
        # pwb_item = wikidatabot.pywikibot.ItemPage(wikidatabot.repo, 'Q43781672')
        # logger.info(pwb_item)
        pwb_item.get()
        # pwb_item_id = pwb_item.getID()
        logger.info(f"Item: {pwb_item.getID()}")
        item = Item.from_pwb(pwb_item)

        ine_code = get_ine_code(item, INE_MUNICIPALITY_CODE)
        if not ine_code:
            logger.error(f"No INE code in item {item.id}")
            continue
        elif ine_code not in to_ine_code_value:
            logger.error(f"No INE code in file: file does not contain INE code {ine_code}, present in item {item.id}")
            continue
        elif ine_code in used_ine_codes:
            logger.error(f"Duplicated INE code: INE code {ine_code} is present in items {item.id} and "
                         f"{used_ine_codes[ine_code]}")
            continue
        else:
            logger.info(f"INE code {ine_code} in item {item.id}")
            official_name_value = to_ine_code_value[ine_code]
            used_ine_codes[ine_code] = item.id

        if i >= 0 and args.debug:
            break

    unused_ine_codes = to_ine_code_value.keys() - used_ine_codes.keys()
    if unused_ine_codes and not args.debug:
        logger.error(f"Unused INE codes: code file contains unused INE codes "
                     f"{list(unused_ine_codes)}")

    logger.info('END check_ine_code')
