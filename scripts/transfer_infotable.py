"""
https://ca.wikipedia.org/wiki/Viquip%C3%A8dia:Consultes_de_manteniment/Wikidata #Paràmetres manuals d'Infotaules a traspassar a WD

https://ca.wikipedia.org/wiki/Plantilla:Infotaula_persona/%C3%BAs


%run scripts/transfer_infotable.py --debug
%run scripts/transfer_infotable.py --debug  --log logs/transfer_infotable-01.log

TEST:
%run scripts/harvest_template.py -lang:ca -family:wikipedia -cat:"Articles amb càrrecs manuals i P39" -template:"Infotaula persona" -namespace:0 carrec P39

"""
import argparse
import datetime
import logging
import re
from collections import defaultdict

import pywikibot as pw
from pywikibot import pagegenerators as pg
import wikidatabot
from wikidatabot.models import Claim, Statement, Item


logger = logging.getLogger("transfer_infotable")


CA_SITE = pw.Site('ca', 'wikipedia')
EN_SITE = pw.Site('en', 'wikipedia')
ES_SITE = pw.Site('es', 'wikipedia')
GL_SITE = pw.Site('gl', 'wikipedia')

# Constants

# Infotable parameters
POSITION_HELD = 'P39'
# Qualifiers
START_TIME = 'P580'
END_TIME = 'P582'
REPLACES = 'P1365'
REPLACED_BY = 'P1366'
#
COAT_OF_ARMS_IMAGE = 'P94'
SEAL_IMAGE = 'P158'
#
ELECTED_IN = 'P2715'
ELECTORAL_DISTRICT = 'P768'
PARLIAMENTARY_TERM = 'P2937'  # not in Infotaula
PARLIAMENTARY_GROUP = 'P4100'  # not in Infotaula
APPOINTED_BY = 'P748'
#
CABINET = 'P5054'
#
SERIES_ORDINAL = 'P1545'
CONFERRED_BY = 'P1027'
OF = 'P642'
TOGETHER_WITH = 'P1706'
END_CAUSE = 'P1534'
#
DIOCESE = 'P708'

# Resources
IMPORTED_FROM_WIKIMEDIA_PROJECT = 'P143'
CATALAN_WIKIPEDIA = 'Q199693'
RETRIEVED = 'P813'

# Utils to find position from organization
OFFICE_HELD_BY_HEAD_OF_GOVERNMENT = 'P1313'
OFFICE_HELD_BY_HEAD_OF_THE_ORGANIZATION = 'P2388'
OFFICE_HELD_BY_HEAD_OF_STATE = 'P1906'
HAS_PART = 'P527'
HAS_PARTS_OF_THE_CLASS = 'P2670'

# Utils to find position from list
IS_A_LIST_OF = 'P360'
HUMAN = 'Q5'

# Utils to fix electoral district
MEMBER_OF_EUROPEAN_PARLIAMENT = 'Q27169'
MEMBER_OF_PARLIAMENT_OF_BALEARIC_ISLANDS = 'Q28137076'
MEMBER_OF_CORTS_VALENCIANES = 'Q21609684'
# Congress of Deputies
MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN = 'Q18171345'
# Parliament of Catalonia
MEMBER_OF_PARLIAMENT_OF_CATALONIA = 'Q18714088'
PRESIDENT_OF_PARLIAMENT_OF_CATALONIA = 'Q26000995'
# Senate
MEMBER_OF_THE_SENATE_OF_SPAIN = 'Q19323171'

#
MINISTER_OF_THE_NAVY_OF_SPAIN = 'Q15895305'

INFOTABLE_PARAMS = {
    # From: https://ca.wikipedia.org/wiki/Plantilla:Infotaula_persona/%C3%BAs
    'carrec': POSITION_HELD,
    'escut_carrec': COAT_OF_ARMS_IMAGE,
    'inici': START_TIME,
    'final': END_TIME,
    'predecessor': REPLACES,
    'successor': REPLACED_BY,
    'k_etiqueta': None,
    'k_nom': None,
    # From: https://ca.wikipedia.org/wiki/Plantilla:Infotaula_persona?action=edit
    # From: https://ca.wikipedia.org/wiki/Plantilla:Infotaula_de_pol%C3%ADtic/bloc_carrec
    'ordre': SERIES_ORDINAL,
    'junt_a': TOGETHER_WITH,
    'nominat': APPOINTED_BY,
    'designat': APPOINTED_BY,
    'a_etiqueta': None,
    'a_nom': None,
    'b_etiqueta': None,
    'b_nom': None,
    'e_etiqueta': None,
    'e_nom': None,
    'f_etiqueta': None,
    'f_nom': None,
    'l_etiqueta': None,
    'l_nom': None,
}

# Regex
DIGIT_REGEX = re.compile(r"(\d+)")
LINK_REGEX = re.compile(r'\[\[(?P<link>[^\]|[<>{}]*)(?:\|(?P<text>.*?))?\]\]')
ORDINAL_REGEX = re.compile(r"(\d+)[rntéèa]\.? .+")
PREPOSITION_REGEX = re.compile(r"(?: de | d'|\s)")

COUNTRIES = ["Espanya", "França", "Portugal", "Regne_Unit"]
AMBASSADOR_OF_SPAIN_TO_FRANCE = 'Q27969744'
AMBASSADOR_OF_SPAIN_TO_PORTUGAL = 'Q37140063'
AMBASSADOR_OF_SPAIN_TO_THE_UNITED_KINGDOM = 'Q43542408'
AMBASSADOR_OF_TO = {
    ("Espanya", "França"): AMBASSADOR_OF_SPAIN_TO_FRANCE,
    ("Espanya", "Portugal"): AMBASSADOR_OF_SPAIN_TO_PORTUGAL,
    ("Espanya", "Regne_Unit"): AMBASSADOR_OF_SPAIN_TO_THE_UNITED_KINGDOM,
}
SULTAN_OF_MOROCCO = 'Q14566713'

ARCHBISHOP, CATHOLIC_ARCHBISHOP = ('Q49476', 'Q48629921')
COUNTY_OF_CARCASSONNE,  COUNT_OF_CARCASSONNE = ('Q38697063', 'Q38697206')
KINGDOM_OF_ISRAEL, KING_OF_ISRAEL = ('Q230407', 'Q26835654')
KINGDOM_OF_JUDAH, KING_OF_JUDAH = ('Q48685', 'Q10550167')
FIX_POSITION_VALUE = {
    ARCHBISHOP: CATHOLIC_ARCHBISHOP,
    COUNTY_OF_CARCASSONNE: COUNT_OF_CARCASSONNE,
    KINGDOM_OF_ISRAEL: KING_OF_ISRAEL,
    KINGDOM_OF_JUDAH: KING_OF_JUDAH,
}

CONSTITUENCY_OF_EUROPEAN_PARLIAMENT = {
    "Espanya": 'Q16254367',
}

OLD_CONSTITUENCY_OF_CONGRESS_OF_SPAIN = {
    "Ágreda": 'Q38604699',
    "Albaida": 'Q36116919',
    "Albarrasí": 'Q38708258',
    "Albocàsser": 'Q40447215',
    "Albuñol": 'Q39398038',
    "Alcalá de Henares": 'Q39999310',
    "Alcántara": 'Q40999671',
    "Alcañices": 'Q41333120',
    "Alcaraz": 'Q40339455',
    "Alcázar de San Juan": 'Q40668523',
    "Almadén": 'Q40668817',
    "Almagro": 'Q40668015',
    "Almansa": 'Q40339812',
    "Almendralejo": 'Q41000377',
    "Alzira": 'Q36117345',
    "Aracena": 'Q42887433',
    "Arenys de Mar": 'Q39493445',
    "Balaguer": 'Q41799543',
    "Benavente": 'Q41333371',
    "Berga": 'Q39494993',
    "Berja": 'Q42294813',
    "Brihuega": 'Q43188696',
    "Cañete": 'Q40224179',
    "Cartagena": 'Q42108193',
    "Casas Ibáñez": 'Q40338775',
    "Castellterçol": 'Q41726769',
    "Castuera": 'Q38996218',
    "Cervera": 'Q41799550',
    "Chinchón": 'Q39998148',
    "Cieza": 'Q42108059',
    "Còria": 'Q38984195',
    "Daimiel": 'Q43188438',
    "Daroca": 'Q42755686',
    "Don Benito": 'Q38984754',
    "Écija": 'Q42294721',
    "Enguera": 'Q36118957',
    "Estella": 'Q42318353',
    "Estepa": 'Q42208655',
    "Falset": 'Q65210002',
    "Fraga": 'Q42755783',
    "Gandesa": 'Q41726332',
    "Gandia": 'Q36119335',
    "Gaucín": 'Q42294745',
    "Getafe": 'Q39998553',
    "Gràcia": 'Q65210007',
    "Granada": 'Q42294799',  # TODO
    "Granollers": 'Q39762908',
    "Grazalema": 'Q39645003',
    "Guadix": 'Q43140180',
    "Huelva": 'Q42887399',  # TODO
    "Huete": 'Q40225238',
    "Igualada": 'Q65209993',
    "Illescas": 'Q38025634',
    "Laguardia": 'Q40078644',
    "Lillo": 'Q38138718',
    "Llerena": 'Q43229776',
    "Llíria": 'Q36120327',
    "Loja": 'Q43140042',
    "Manresa": 'Q41764614',
    "Monòver": 'Q87163933',
    "Móra de Rubiols": 'Q38710029',
    "Olot": 'Q65209995',
    "Purchena": 'Q86835202',
    "Requena": 'Q36120909',
    "Sagunt": 'Q36121470',
    "Seu d'Urgell": 'Q41663408',
    "Solsona": 'Q41663518',
    "Sort": 'Q41686256',
    "Sueca": 'Q36122268',
    "Tarancón": 'Q40226417',
    "Terrassa": 'Q41794174',
    "Tolosa": 'Q41591455',
    "Toro": 'Q41333616',
    "Torrent": 'Q36122740',
    "Tortosa": 'Q41686133',
    "Tremp": 'Q41663641',
    "València": 'Q36123773',  # TODO: this is overwritten
    "Valls": 'Q41627234',
    "Valverde del Camino": 'Q42887354',
    "Vendrell": 'Q41627356',
    "el Vendrell": 'Q41627356',
    "Verín": 'Q42899630',
    "Vic": 'Q63247018',
    "Vigo": 'Q42899708',
    "Vila Joiosa": 'Q42670537',
    "Vilafranca del Panedés": 'Q41627082',
    "Villena": 'Q42666772',
    "Vitòria": 'Q40077587',
    "Viveiro": 'Q42899469',
    "Xàtiva": 'Q36119899',
    "Xelva": 'Q36117931',
    "Xiva": 'Q36118361',
    "Zumaia": 'Q41591337',
}

CONSTITUENCY_OF_CONGRESS_OF_SPAIN = {
    **OLD_CONSTITUENCY_OF_CONGRESS_OF_SPAIN,
    "Àlaba": 'Q8076636',
    "Alacant": 'Q939475',
    "Albacete": 'Q21402519',
    "Almeria": 'Q4733797',
    "Astúries": 'Q4811764',
    "Àvila": 'Q8077017',
    "Badajoz": 'Q4840525',
    "Illes Balears": 'Q4850673',
    "Barcelona": 'Q4859840',
    "Biscaia": 'Q4917218',
    "Burgos": 'Q4998668',
    "Càceres": 'Q5202311',
    "Cadis": 'Q2887470',
    "Cantàbria": 'Q5033517',
    "Castelló": 'Q5049705',
    "Ceuta": 'Q5065729',
    "Ciudad Real": 'Q5124161',
    "Conca": 'Q5192583',
    "Còrdova": 'Q5202717',
    "la Corunya": 'Q4656117',
    "Girona": 'Q5564804',
    "Granada": 'Q5594085',
    "Guadalajara": 'Q5613179',
    "Guipúscoa": 'Q5564085',
    "Huelva": 'Q8346385',
    "Jaén": 'Q6168504',
    "Lleida": 'Q6661991',
    "Lleó": 'Q6538224',
    "Lugo": 'Q6699826',
    "Madrid": 'Q6728617',
    "Màlaga": 'Q5680327',
    "Melilla": 'Q6812414',
    "Múrcia": 'Q6937568',
    "Navarra": 'Q6982118',
    "Osca": 'Q5929316',
    "Ourense": 'Q7111276',
    "Palència": 'Q7127111',
    "Pontevedra": 'Q7228193',
    "Las Palmas": 'Q6492379',
    "La Rioja": 'Q6464884',
    "Salamanca": 'Q19632195',
    "Santa Cruz de Tenerife": 'Q7419451',
    "Saragossa": 'Q8066573',
    "Segòvia": 'Q7446308',
    "Sevilla": 'Q7458064',
    "Sòria": 'Q7563479',
    "Tarragona": 'Q7686643',
    "Terol": 'Q7705300',
    "Toledo": 'Q7814141',
    "València": 'Q4888883',
    "Valladolid": 'Q7911798',
    "Zamora": 'Q8065895',
}

CONSTITUENCY_OF_SENATE_OF_SPAIN = {
    "Àlaba": 'Q58213992',
    "Alacant": 'Q58214005',
    "Albacete": 'Q58213998',
    "Almeria": 'Q58214012',
    "Astúries": 'Q58214016',
    "Àvila": 'Q58136360',
    "Badajoz": 'Q58214023',
    "Barcelona": 'Q58214028',
    "Biscaia": 'Q58214031',
    "Burgos": 'Q58214034',
    "Càceres": 'Q58214040',
    "Cadis": 'Q58214045',
    "Cantàbria": 'Q58214049',
    "Castelló": 'Q58214058',
    "Ceuta": 'Q58214063',
    "Ciudad Real": 'Q58214072',
    "Conca": 'Q58214085',
    "Còrdova": 'Q58214078',
    "la Corunya": 'Q58213651',
    "Eivissa-Formentera": 'Q58214093',
    "Girona": 'Q58214114',
    "Granada": 'Q58214123',
    "Guadalajara": 'Q58214130',
    "Guipúscoa": 'Q58214104',
    "Huelva": 'Q58214140',
    "Jaén": 'Q58214143',
    "Lleida": 'Q58214164',
    "Lleó": 'Q58214155',
    "Lugo": 'Q58214170',
    "Madrid": 'Q58137354',
    "Màlaga": 'Q58214180',
    "Mallorca": 'Q58214191',
    "Melilla": 'Q58214198',
    "Menorca": 'Q21480830',
    "Múrcia": 'Q58214212',
    "Navarra": 'Q58214221',
    "Osca": 'Q75170261',
    "Ourense": 'Q58214230',
    "Palència": 'Q58214244',
    "La Palma": 'Q21480772',
    "Pontevedra": 'Q58214253',
    "La Rioja": 'Q58214151',
    "Salamanca": 'Q58214261',
    "Saragossa": 'Q58214320',
    "Segòvia": 'Q58214265',
    "Sevilla": 'Q58214271',
    "Sòria": 'Q58214279',
    "Tarragona": 'Q58214284',
    "Terol": 'Q58214292',
    "Toledo": 'Q58214299',
    "València": 'Q58214307',
    "Valladolid": 'Q58135859',
    "Zamora": 'Q58214314',
}

CONSTITUENCY_OF_CORTS_VALENCIANES = {
    "Alacant": 'Q30601105',
    "Castelló": 'Q30601107',
    "València": 'Q30601109',
}

CONSTITUENCY_OF_PARLIAMENT_OF_BALEARIC_ISLANDS = {
    "Formentera": 'Q30600685',
    "Eivissa": 'Q30600686',
    "Mallorca": 'Q30600688',
    "Menorca": 'Q30600684',
}

CONSTITUENCY_OF_PARLIAMENT_OF_CATALONIA = {
    "Barcelona": 'Q28496610',
    "Girona": 'Q24932380',
    "Lleida": 'Q24932382',
    "Tarragona": 'Q24932383',
}

CONSTITUENCY_REPRESENTED_BY = {
    MEMBER_OF_EUROPEAN_PARLIAMENT: CONSTITUENCY_OF_EUROPEAN_PARLIAMENT,
    MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN: CONSTITUENCY_OF_CONGRESS_OF_SPAIN,
    MEMBER_OF_THE_SENATE_OF_SPAIN: CONSTITUENCY_OF_SENATE_OF_SPAIN,
    MEMBER_OF_PARLIAMENT_OF_BALEARIC_ISLANDS: CONSTITUENCY_OF_PARLIAMENT_OF_BALEARIC_ISLANDS,
    MEMBER_OF_PARLIAMENT_OF_CATALONIA: CONSTITUENCY_OF_PARLIAMENT_OF_CATALONIA,
    MEMBER_OF_CORTS_VALENCIANES: CONSTITUENCY_OF_CORTS_VALENCIANES,
}


TO_MONTH_NUMBER = {
    'gener': 1, 'febrer': 2, 'març': 3, 'abril': 4, 'maig': 5, 'juny': 6, 'juliol': 7, 'agost': 8, 'setembre': 9,
    'octubre': 10, 'novembre': 11, 'desembre': 12
}


def parse_args():
    parser = argparse.ArgumentParser(description="Transfer infotable")
    parser.add_argument('--log', default='')
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args()


def config_logger(log_filename='', debug=False):
    # Set logging level
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)8s] %(message)s')
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(ch)
    if log_filename:
        # Create file handler
        fh = logging.FileHandler(filename=log_filename, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def create_generator(category='Categoria:Articles amb càrrecs manuals i P39', groupsize=50):  # lang='ca', family='wikipedia',
    site = CA_SITE
    cat = pw.Category(site, category)
    pages = cat.articles()
    return pg.PreloadingGenerator(pages, groupsize=groupsize)


def parse_infotable(page, infotable="Infotaula persona"):
    def get_redirects(title):
        temp = pw.Page(CA_SITE, title, ns=10)
        if temp.isRedirectPage():
            temp = temp.getRedirectTarget()
        titles = [page.title(with_ns=False).lower()
                  for page in temp.getReferences(filter_redirects=True, namespaces=[10], follow_redirects=False)]
        titles.append(temp.title(with_ns=False).lower())
        return titles
    infotable = infotable.replace('_', ' ')
    infotables = get_redirects(infotable)
    templates = pw.textlib.extract_templates_and_params(page.text, True, True)
    for template_name, template_params in templates:
        if template_name.lower() in infotables:
            return template_params
    # else:
    #     return templates


def extract_positions(template_params):
    positions = defaultdict(dict)
    for param_name, param_value in template_params.items():
        param_name, *param_num = DIGIT_REGEX.split(param_name)
        param_num = param_num[0] if param_num else '1'
        if param_name in INFOTABLE_PARAMS:
            positions[param_num][param_name] = param_value
    if not positions:
        return []
    positions = [positions[position_num] for position_num in sorted(positions)]
    # Propagate values
    for i, position in enumerate(positions):
        # Propagate 'carrec'
        if 'carrec' not in position:
            position['carrec'] = positions[i - 1]['carrec']
        # Propagate year from final to inici
        if 'inici' in position and 'final' in position:
            # kaka
            inici = position['inici']
            if not inici.startswith('{{'):
                inici = inici.replace('[[', '').replace(']]', '')
                inici_parts = PREPOSITION_REGEX.split(inici)[::-1]
                if inici_parts[0].isalpha():
                    final = position['final']
                    if not final.startswith('{{'):
                        final = final.replace('[[', '').replace(']]', '')
                        final_parts = PREPOSITION_REGEX.split(final)[::-1]
                        if not final_parts[0].isalpha():
                            position['inici'] += " de " + final_parts[0]
    return positions


def get_page_from_link(link, langs=None):
    if not langs:
        langs = ['ca', 'es', 'gl', 'en']
    sites = {'ca': CA_SITE, 'es': ES_SITE, 'gl': GL_SITE, 'en': EN_SITE}
    logger.info(f"Get page from link {link}")
    for lang in langs:
        site = sites[lang]
        page = pw.Page(pw.Link(link, source=site))
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        if page.exists():
            logger.info(f"Found Wikipedia page from {lang} page link {link}: {page}")
            return page
        else:
            logger.warning(f"No Wikipedia page from {lang} page link {link}")
    logger.error(f"No Wikipedia page from (ca, es, gl, en) page links: {link}")


def get_item_from_page(page):
    logger.info(f"Get item from page {page}")
    try:
        item = pw.ItemPage.fromPage(page)
    except pw.NoPage:
        logger.error(f"No Wikidata item from page: {page}")
        return
    logger.info(f"Found Wikidata item from page {page}: {item}")
    return item


def get_item_from_page_link(link, langs=None):
    logger.info(f"Get item from page link {link}")
    page = get_page_from_link(link, langs=langs)
    if not page:
        logger.error(f"No Wikidata item because no Wikipedia page from page link: {link}")
        return
    item = get_item_from_page(page)
    return item


def get_item_from_id(item_id):
    logger.info(f"Get item from id {item_id}")
    try:
        item = pw.ItemPage(wikidatabot.repo, item_id)
    except pw.NoPage:
        logger.error(f"No Wikidata item from id {item_id}")
        return
    logger.info(f"Found Wikidata item from id {item_id}")
    return item


# def get_item(page):
#     logger.info(f"Get item from {page}")
#     if isinstance(page, str):
#         link = page
#         page = get_page_from_link(link)
#     if not page:
#         logger.error(f"No Wikidata item because no Wikipedia page from link: {link}")
#         return
#     item = get_item_from_page(page)
#     return item


def get_office_held_by_head_from_page(page, of=None):
    logger.info(f"Get office held by head from page {page}")
    if not page:
        logger.error(f"No page")
        return
    if page.title().lower().startswith("llista"):
        logger.warning(f"Link is a list")
    organization_item = get_item_from_page(page)
    if not organization_item:
        logger.error(f"No organization item found from page {page}")
        return
    if of == 'state':
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_STATE)
    else:
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_GOVERNMENT)
        if not office_claims:
            office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_THE_ORGANIZATION)
    if office_claims:
        if len(office_claims) == 1:
            position_item = office_claims[0].getTarget()  # .id
        else:
            logger.error(f"More than one office held by head found for item {organization_item}")
            return
    else:
        logger.error(f"No office held by head found for item {organization_item}")
        return
    return position_item


def get_office_held_by_head_from_link(link, of=None):
    logger.info(f"Get office held by head from link {link}")
    if not link:
        logger.error(f"No link")
        return
    if link.lower().startswith("llista"):
        logger.warning(f"Link is a list")
    organization_item = get_item_from_page_link(link)
    if not organization_item:
        logger.error(f"No organization item found from link {link}")
        return
    if of == 'state':
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_STATE)
    else:
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_GOVERNMENT)
        if not office_claims:
            office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_THE_ORGANIZATION)
    if office_claims:
        if len(office_claims) == 1:
            position_item = office_claims[0].getTarget()  # .id
        else:
            logger.error(f"More than one office held by head found for item {organization_item}")
            return
    else:
        logger.error(f"No office held by head found for item {organization_item}")
        return
    return position_item


def get_office_held_by_head(organization_page, head_of=None, from_list_of=None, prepend_to_list_of=None):
    logger.info(f"Get office held by head from organization: {organization_page}")
    if not organization_page:
        logger.error(f"No organization: {organization_page}")
        return
    if isinstance(organization_page, str):
        organization_link = organization_page
        organization_page = get_page_from_link(organization_link)
        if not organization_page:
            logger.error(f"No Wikidata item because no Wikipedia page from link: {organization_link}")
            return
    # From list of
    if from_list_of and (organization_page.title().lower().startswith("llista") or
                         organization_page.title().lower().startswith(from_list_of + "s")):
        organization_page = get_organization_page_from_list_link(organization_page.title(), from_list_of,
                                                                 prepend=prepend_to_list_of)
        if not organization_page:
            logger.error(f"No organization page from list link: {organization_page}")
            return
    # Organization item
    organization_item = get_item_from_page(organization_page)
    if not organization_item:
        logger.error(f"No organization item found from organization: {organization_page}")
        return
    if head_of == 'state':
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_STATE)
    else:
        office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_GOVERNMENT)
        if not office_claims:
            office_claims = organization_item.claims.get(OFFICE_HELD_BY_HEAD_OF_THE_ORGANIZATION)
    if office_claims:
        if len(office_claims) == 1:
            position_item = office_claims[0].getTarget()  # .id
        else:
            logger.error(f"More than one office held by head found for item {organization_item}")
            return
    else:
        logger.error(f"No office held by head found for item {organization_item}")
        return
    return position_item


def get_has_part_from_link(link):
    logger.info(f"Get has part from link {link}")
    if not link:
        logger.error(f"No link")
        return
    if link.lower().startswith("llista"):
        logger.warning(f"Link is a list")
    organization_item = get_item_from_page_link(link)
    if not organization_item:
        logger.error(f"No organization item found from link {link}")
        return
    part_claims = organization_item.claims.get(HAS_PART)
    if not part_claims:
        part_claims = organization_item.claims.get(HAS_PARTS_OF_THE_CLASS)
    if part_claims:
        if len(part_claims) == 1:
            position_item = part_claims[0].getTarget()  # .id
        else:
            logger.error(f"More than one part found for item {organization_item}")
            return
    else:
        logger.error(f"No part found for item {organization_item}")
        return
    return position_item


def parse_date(value):
    logger.info(f"Parse date")
    if value.startswith('{{'):
        date_parts = value.replace('{{', '').replace('}}', '').split('|')
        date_parts = date_parts[1:] if len(date_parts) > 1 else []
    else:
        value = value.replace('[[', '').replace(']]', '')
        date_parts = PREPOSITION_REGEX.split(value)[::-1]
    if len(date_parts) < 1 or len(date_parts) > 3 or date_parts[0].isalpha():  # ["març", 13]
        logger.error(f"Failed parsing date: {value}")
        return
    date_parts = [int(part) if part.isdigit() else TO_MONTH_NUMBER[part] for part in date_parts
                  if part.isdigit() or part in TO_MONTH_NUMBER]
    claim_value = {k: v for k, v in zip(['year', 'month', 'day'], date_parts)}
    return claim_value


def get_organization_link_from_list_link(link, word, prepend=None):
    logger.info(f"Get organization link from list link {link}, using word {word}")
    pattern = r".*" + word + r"\w+ (?P<preposition>de la |del|de l' |de |d')(?P<organization>.+)"
    match = re.match(pattern, link, re.I)
    if not match:
        logger.error(f"Failed getting organization link from list link {link}, using word {word}")
        return
    organization_link = match.group('organization')
    if prepend:
        # To cope with: Llista de ministres [(d')(Hisenda)] -> Llista de ministres del [Ministeri (d')(Hisenda)]
        organization_link = f"{prepend} {match.group('preposition')}{organization_link}"
    logger.info(f"Got organization link {organization_link} from list link {link}")
    return organization_link


def get_organization_page_from_list_link(link, word, prepend=None):
    logger.info(f"Get organization page from list link: {link}")
    organization_link = get_organization_link_from_list_link(link, word, prepend=prepend)
    if not organization_link:
        logger.error(f"No organization link from list link: {link}")
        return
    organization_page = get_page_from_link(organization_link)
    if not organization_page:
        logger.error(f"No organization page from organization link: {organization_link}")
        return
    return organization_page


def parse_position_value(position_value):
    logger.info(f"Parse position value: {position_value}")
    position_item = None
    position_claim = None
    qualifiers = []
    # Match links
    matched_links = LINK_REGEX.findall(position_value)
    # From links
    if matched_links:
        position_link = matched_links[0][0].strip()
        position_page = get_page_from_link(position_link)
        position_page_title = position_page.title() if position_page else ''
        position_text = matched_links[0][1].strip()
        if not position_text:
            position_text = position_value
        # No page link
        if not position_page_title:
            position_item = None
        # Page link
        elif position_text.lower().startswith("[["):
            if position_page_title.lower().startswith("llista"):
                position_item = get_list_of(position_page)
            else:
                position_item = get_item_from_page(position_page)
        # alcalde
        elif position_text.lower().startswith("alcalde"):
            if position_page_title.lower().startswith("alcalde"):
                position_item = get_item_from_page(position_page)
            else:
                position_item = get_office_held_by_head(position_page, from_list_of="alcalde")
        # diputa
        elif position_text.lower().startswith("diputa"):
            if position_page_title == "Parlament de Catalunya":
                position_item = MEMBER_OF_PARLIAMENT_OF_CATALONIA
            else:
                position_item = get_has_part_from_link(position_link)
        # governador
        elif position_page_title.lower().startswith("governador"):
            if len(matched_links) == 2:
                state_link = matched_links[1][0].strip()
                position_item = get_office_held_by_head_from_link(state_link)
        # khediv
        elif position_page_title.lower().startswith("khediv") or position_page_title.lower().startswith("kediv"):
                position_item = get_item_from_page(position_page)
        # membre
        elif position_text.lower().startswith("membre"):
            position_item = get_has_part_from_link(position_link)
        # ministr
        elif position_text.lower().startswith("ministr"):
            if position_page_title.lower().startswith("ministr"):
                position_item = get_item_from_page(position_page)
            else:
                position_item = get_office_held_by_head(position_page, from_list_of="ministr",
                                                        prepend_to_list_of="Ministeri")
        # president
        elif position_text.lower().startswith("president") or "president" in position_text.lower():
            if position_page_title.lower().startswith("president"):
                position_item = get_item_from_page(position_page)
            else:
                # TODO: of='state'?
                position_item = get_office_held_by_head(position_page, from_list_of="president")
        # # regidor  # TODO: not yet a clearly established structure in Wikidata
        # elif position_text.lower().startswith("regidor"):
        #     position_item = get_has_part_from_link(position_link)
        # rei
        elif position_text.lower().startswith("rei"):
            if position_page_title.lower().startswith("rei") and not \
                    position_page_title.lower().startswith("rei" + "s"):
                position_item = get_item_from_page(position_page)
            else:
                position_item = get_office_held_by_head(position_page, head_of="state", from_list_of="rei")
        # secretari
        elif position_text.lower().startswith("secretari d") or position_text.lower().startswith("secretària d"):
            if position_page_title.lower().startswith("secretari d"):
                position_item = get_item_from_page(position_page)
        # senador
        elif position_text.lower().startswith("senador"):
            if position_page_title == "Senat d'Espanya":
                position_item = MEMBER_OF_THE_SENATE_OF_SPAIN
        # Position claim
        if not position_item:
            logger.error(f"Failed parsing position value: {position_value}")
        # Eventual qualifiers in position value
        if len(matched_links) >= 2:
            logger.info("Parse eventual qualifiers in position value")
            for matched_link in matched_links[1:]:
                qualifier_property = None
                qualifier_item = None
                if len(matched_links) == 2 and 'designa' in position_value:
                    logger.info(f"Parse appointed by")
                    qualifier_property = APPOINTED_BY
                    qualifier_link = matched_link[0].strip()
                    qualifier_item = get_item_from_page_link(qualifier_link)
                if "arquebisbat" in matched_link[0].lower():
                    logger.info(f"Parse diocese")
                    qualifier_property = DIOCESE
                    qualifier_link = matched_link[0].strip()
                    qualifier_item = get_item_from_page_link(qualifier_link)
                if len(matched_links) == 2 and " per " in position_value and ('diputa' in position_value.lower()
                                                                              or 'senador' in position_value.lower()):
                    logger.info(f"Parse electoral district")
                    qualifier_property = ELECTORAL_DISTRICT
                    position_item_id = position_item if isinstance(position_item, str) else position_item.id
                    qualifier_item = get_fixed_electoral_district(matched_link, position_value_id=position_item_id)
                if qualifier_item:
                    qualifier_claim = Claim(property=qualifier_property, item=qualifier_item)
                    logger.info(f"Qualifier claim: {qualifier_claim.value}")
                    qualifiers.append(qualifier_claim)
        if position_value[0].isdigit() or position_text[0].isdigit():
            value = position_value if position_value[0].isdigit() else position_text
            match = ORDINAL_REGEX.match(value)
            if match:
                series_ordinal_quantity = match.group(1)  # must be value=str
                series_ordinal_claim = Claim(property=SERIES_ORDINAL, value=series_ordinal_quantity)
                logger.info(f"Series ordinal claim: {series_ordinal_claim.value}")
                qualifiers.append(series_ordinal_claim)
    # Without links
    else:
        if position_value.lower().startswith("alcalde"):
            regex = "alcalde" + r"\S*\s(?:de |d')(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                position_item = get_office_held_by_head_from_link(match.group('organization'))
        elif position_value.lower().startswith("president"):
            regex = "president" + r"\S*\s(?:de la |de |d'|del )(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                organization = match.group('organization')
                if organization == "Malta":
                    organization = "República de Malta"
                position_item = get_office_held_by_head_from_link(organization, of='state')
        elif position_value.lower().startswith("primer ministr") or \
                position_value.lower().startswith("primera ministr"):
            regex = "primera? ministr" + r"\S*\s(?:de la |de |d'|del )(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                position_item = get_office_held_by_head_from_link(match.group('organization'))
        elif position_value.lower().startswith("rei"):
            regex = "rei" + r"\S*\s(?:de |d')(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                position_item = get_office_held_by_head_from_link(match.group('organization'), of='state')
        elif position_value.lower().startswith("ambaixador"):
            # Join multi-word countries
            position_value = position_value.replace("Regne Unit", "Regne_Unit")
            words = re.split(r"[\s']", position_value)
            of_to = tuple(word for word in words if word in COUNTRIES)
            if len(of_to) != 2:
                logger.error(f"Failed parsing 'ambaixador': not a pair of countries found {of_to}")
            else:
                if of_to not in AMBASSADOR_OF_TO:
                    logger.error(f"Missing ambassador of_to {of_to}")
                else:
                    position_item = AMBASSADOR_OF_TO.get(of_to)
        elif position_value.lower().startswith("soldà"):
            regex = "soldà" + r"\S*\s(?:de la |de |d'|del )(?P<organization>.+)"
            match = re.match(regex, position_value, re.I)
            if match:
                organization = match.group('organization')
                if organization == "Marroc":
                    position_item = SULTAN_OF_MOROCCO
        if not position_item:
            logger.error(f"Failed parsing position value: {position_value}")
    if position_item:
        position_item_id = position_item if isinstance(position_item, str) else position_item.id
        if position_item_id in FIX_POSITION_VALUE:
            position_item = FIX_POSITION_VALUE[position_item_id]
        position_claim = Claim(property=POSITION_HELD, item=position_item)
        logger.info(f"Position held claim: {position_claim.value}")
    return position_claim, qualifiers


def parse_position_qualifier(key, value, position_value_id=''):
    logger.info(f"Parse position qualifier: {key}: {value}")
    claim_value = None
    # Equivalences
    if key.lower() == "proclamació":
        key = "inici"
    # Standard cases
    if key == 'escut_carrec':
        # Ignore it: this should be in the position item
        logger.warning(f"Skip position qualifier because of key 'escut_carrec': value: {value}")
        return 'CONTINUE'
    elif key == 'inici' or key == 'final':
        if value == "present" or value == "?":
            # Ignore it: this is uninformative
            logger.warning(f"Skip position qualifier because of value 'present': key: {key}")
            return 'CONTINUE'
        # Date
        claim_value = parse_date(value)
    elif key == 'predecessor' or key == 'successor':
        if value == "-":
            # Ignore it: this is uninformative
            logger.warning(f"Skip position qualifier because of value '-': key: {key}")
            return 'CONTINUE'
        # Item
        logger.info(f"Parse as item")
        matches = LINK_REGEX.findall(value)
        if not matches:
            logger.error(f"Failed parsing as item: {value}")
            return
        else:
            claim_link = matches[0][0].strip()
            claim_item = get_item_from_page_link(claim_link)
            if claim_item:
                claim_value = {'item': claim_item}
    elif key == 'junt_a':
        # Item
        logger.info(f"Parse as item")
        matches = LINK_REGEX.findall(value)
        if not matches:
            logger.error(f"Failed parsing as item: {value}")
            return
        else:
            claim_link = matches[0][0].strip()
            claim_item = get_item_from_page_link(claim_link)
            if claim_item:
                claim_value = {'item': claim_item}
    # Additional cases
    elif key.lower() == "circumscripció":
        # Item
        logger.info(f"Parse as item")
        claim_item = get_fixed_electoral_district(value, position_value_id=position_value_id)
        if not claim_item:
            logger.error(f"Failed parsing as item: {value}")
            return
        claim_value = {'item': claim_item}
        claim_property = ELECTORAL_DISTRICT
    else:
        # TODO: ordre, junt_a, nominat, designat
        logger.error(f"Unforeseen case for position qualifier: {key}: {value}")
        return
    if claim_value:
        logger.info(f"Found claim value {claim_value} for position qualifier: {key}: {value}")
        if key in INFOTABLE_PARAMS:
            qualifier_claim = Claim(property=INFOTABLE_PARAMS[key], **claim_value)
        else:
            qualifier_claim = Claim(property=claim_property, **claim_value)
    else:
        logger.error(f"No claim value found for position qualifier: {key}: {value}")
        return
    return qualifier_claim


def get_fixed_electoral_district(electoral_district, position_value_id=''):
    logger.info(f"Parse and fix electoral district")
    if isinstance(electoral_district, tuple):
        matches = [electoral_district]
    else:
        matches = LINK_REGEX.findall(electoral_district)
    if matches:
        electoral_district_link = matches[0][0].strip()
        electoral_district_text = matches[0][1].strip()
        if not electoral_district_text:
            electoral_district_text = electoral_district_link
    else:
        electoral_district_text = electoral_district
    # Specific
    if position_value_id and position_value_id in CONSTITUENCY_REPRESENTED_BY:
        electoral_district_id = CONSTITUENCY_REPRESENTED_BY[position_value_id].get(electoral_district_text)
        if electoral_district_id:
            logger.info(f"Found electoral district {electoral_district_id} in specific constituency list")
            electoral_district_item = get_item_from_id(electoral_district_id)
            if electoral_district_item:
                return electoral_district_item
    # Generic
    if not matches:
        if electoral_district_text.lower()[0] in ['a', 'e', 'i', 'o', 'u']:
            electoral_district_link = f"Circumscripció electoral d'{electoral_district_text}"
        else:
            electoral_district_link = f"Circumscripció electoral de {electoral_district_text}"
    electoral_district_item = get_item_from_page_link(electoral_district_link, langs=['ca'])
    return electoral_district_item


def parse_position(position):
    logger.info(f"Parse position: {position}")
    if 'carrec' not in position:
        logger.error(f"Malformed position does not contain 'carrec': {position}")
        return None, []
    position_claim, qualifiers = parse_position_value(position['carrec'])
    if not position_claim:
        logger.error(f"Skip parsing position qualifiers: no position claim found for {position['carrec']}")
        return None, []
    # Position qualifiers
    logger.info("Parse position qualifiers")
    for position_key, position_value in position.items():
        qualifier_claim = None
        # carrec
        if position_key == 'carrec':
            continue
        # k_etiqueta
        elif position_key == 'k_etiqueta':
            label_key = position_key
            label_value = position_value
            name_key = 'k_nom'  # position_key.replace('_etiqueta', '_nom')
            if name_key not in position:
                logger.warning(
                    f"Missing member of k_(label, name) pair: no name {name_key} for label {label_key}: {label_value}")
                continue
            name_value = position[name_key]
            logger.info(f"Parse k_(label, name) pair: ({label_value}, {name_value})")
            qualifier_claim = parse_position_qualifier(label_value, name_value,
                                                       position_value_id=position_claim.value.id)
        elif position_key == 'k_nom':
            name_key = position_key
            name_value = position_value
            label_key = 'k_etiqueta'  # position_key.replace('_nom', '_etiqueta')
            if label_key not in position:
                logger.warning(
                    f"Missing member of k_(label, name) pair: no label {label_key} for name {name_key}: {name_value}")
            continue # already parsed
        # _etiqueta
        elif '_etiqueta' in position_key:
            label_key = position_key
            label_value = position_value
            name_key = position_key.replace('_etiqueta', '_nom')
            if name_key not in position:
                logger.warning(
                    f"Missing member of (label, name) pair: no name {name_key} for label {label_key}: {label_value}")
                continue
            # TODO: parse pair
            name_value = position[name_key]
            logger.warning(f"TODO: Parse (label, name) pair ({label_key}, {name_key}): ({label_value}, {name_value})")
            # return None, []
            continue
        elif '_nom' in position_key:
            name_key = position_key
            name_value = position_value
            label_key = position_key.replace('_nom', '_etiqueta')
            if label_key not in position:
                logger.warning(
                    f"Missing member of (label, name) pair: no label {label_key} for name {name_key}: {name_value}")
            continue  # already parsed
        # rest
        elif position_key in INFOTABLE_PARAMS:
            qualifier_claim = parse_position_qualifier(position_key, position_value)
        else:
            logger.error(f"Unknown position qualifier key, value: {position_key}; {position_value}")
            return None, []
        if not qualifier_claim:
            logger.error(f"No qualifier claim")
            return None, []
        elif qualifier_claim == 'CONTINUE':
            continue
        qualifiers.append(qualifier_claim)
    return position_claim, qualifiers


def get_list_of(list_page):
    logger.info(f"Get list of, from {list_page}")
    list_item = get_item_from_page(list_page)
    if not list_item:
        logger.error(f"No list item found from {list_page}")
        return
    is_a_list_of_statements = list_item.claims.get(IS_A_LIST_OF)
    if not is_a_list_of_statements:
        logger.error(f"No list of statement found for list {list_page}")
        return
    if len(is_a_list_of_statements) != 1:
        logger.error(f"More than one list of statement found for list {list_page}")
        return
    is_a_list_of_item = is_a_list_of_statements[0].target
    if is_a_list_of_item.id == HUMAN:
        logger.info(f"Get qualifier: found list of HUMAN for list {list_page}")
        is_a_list_of_item_qualifiers = is_a_list_of_statements[0].qualifiers
        if len(is_a_list_of_item_qualifiers) != 1:
            logger.error(f"More than one qualifier found for list of HUMAN, for list {list_page}")
            return
        is_a_list_of_item_qualifier_pid, is_a_list_of_item_qualifier_claims = \
            list(is_a_list_of_statements[0].qualifiers.items())[0]
        if len(is_a_list_of_item_qualifier_claims) != 1:
            logger.error(f"More than one qualifier claim found for list of HUMAN qualifier property "
                         f"{is_a_list_of_item_qualifier_pid}, for list {list_page}")
            return
        is_a_list_of_item = is_a_list_of_item_qualifier_claims[0].target
    logger.info(f"Found list of {is_a_list_of_item} for list {list_page}")
    return is_a_list_of_item


def create_position_statements(positions):
    statements = []
    # Parse each position
    for position in positions:
        position_claim, qualifiers = parse_position(position)
        if not position_claim:
            # 1. Create the maximum number of statements
            # logger.error(f"No position claim: skipped position {position}")
            # continue
            # 2. Create either all or no statements
            logger.error(f"Skip all positions: no position claim for position {position}")
            return
        statements.append((position_claim, qualifiers))
    # Create sources
    sources = [Claim(property=IMPORTED_FROM_WIKIMEDIA_PROJECT, item=CATALAN_WIKIPEDIA)]
    today = datetime.date.today()
    today = {'year': today.year, 'month': today.month, 'day': today.day}
    retrieved_claim = Claim(property=RETRIEVED, **today)
    sources.append(retrieved_claim)
    # Create statements
    statements = [Statement(claim=position_claim, qualifiers=qualifiers, sources=sources)
                  for position_claim, qualifiers in statements]
    return statements


def get_main_item(page):
    item = get_item_from_page(page)
    item = Item.from_pwb(item)
    logger.info(f"Main item {item.id} from page: {page}")
    return item


def add_statements(item, statements, summary=''):
    logger.info("Try to add new statements to main item")
    for statement in statements:
        add_statement(item, statement, summary=summary)


def add_statement(item, new_statement, summary=''):
    logger.info(f"Try to add new statement: {new_statement.claim.value.id}")
    duplicated = check_duplicate(item, new_statement, summary=summary)
    if not duplicated:
        logger.info(f"Add statement: {new_statement.claim.value.id}")
        item.add_statement(new_statement, summary=summary)


def check_duplicate(item, new_statement, summary=''):
    logger.info("Check if new statement is duplicated in main item")
    # pwb_item = item._item
    # pwb_new_statement = new_statement._statement
    # New statement
    new_statement_claim_property = new_statement.claim.property
    new_statement_claim_id = new_statement.claim.value.id
    # Item
    if new_statement_claim_property in item.statements:
        statements = item.statements[new_statement_claim_property]
        for statement in statements:
            if new_statement_claim_id == statement.target.id:
                logger.warning(f"Equal position value {new_statement_claim_id} already exists for item {item.id}")
                # TODO: Additional equality conditions
                if not new_statement.qualifiers:
                    logger.info(f"Do not add statement: duplicated position values without qualifiers")
                    return True
                common_qualifier_properties = set(statement.qualifiers.keys()).intersection(
                    {new_statement_qualifier.property for new_statement_qualifier in new_statement.qualifiers})
                if not common_qualifier_properties:
                    # Add new qualifiers
                    logger.info(f"Item position does not contain any of the new statement qualifiers")
                    add_qualifiers(statement, new_statement, summary=summary)
                    return True
                else:
                    equal_qualifiers = True
                    for new_statement_qualifier in new_statement.qualifiers:
                        if new_statement_qualifier.property in common_qualifier_properties:
                            if hasattr(new_statement_qualifier.value, 'id'):
                                new_statement_qualifier_value = new_statement_qualifier.value.id
                            elif hasattr(new_statement_qualifier.value, 'precision'):
                                new_statement_qualifier_value = {'year': new_statement_qualifier.value.year}
                                if new_statement_qualifier.value.precision >= 10:
                                    new_statement_qualifier_value['month'] = new_statement_qualifier.value.month
                                if new_statement_qualifier.value.precision >= 11:
                                    new_statement_qualifier_value['day'] = new_statement_qualifier.value.day
                            else:
                                new_statement_qualifier_value = new_statement_qualifier.value
                            equal_qualifier = False  # if any True:
                            for claim in statement.qualifiers[new_statement_qualifier.property]:
                                if hasattr(claim.target, 'id'):
                                    statement_qualifier_value = claim.target.id
                                elif hasattr(claim.target, 'precision'):
                                    statement_qualifier_value = {'year': claim.target.year}
                                    if claim.target.precision >= 10:
                                        statement_qualifier_value['month'] = claim.target.month
                                    if claim.target.precision >= 11:
                                        statement_qualifier_value['day'] = claim.target.day
                                else:
                                    statement_qualifier_value = claim.target
                                if isinstance(statement_qualifier_value, dict):
                                    if all([
                                        statement_qualifier_value[key] == new_statement_qualifier_value[key] for key in
                                        set(statement_qualifier_value.keys()).intersection(
                                            new_statement_qualifier_value.keys())]):
                                        equal_qualifier = True
                                        break
                                else:
                                    if new_statement_qualifier_value == statement_qualifier_value:
                                        equal_qualifier = True
                                        break
                            equal_qualifiers = equal_qualifiers and equal_qualifier
                            if not equal_qualifiers:  # if any of the common qualifiers are different
                                return False
                    if equal_qualifiers:  # if all common qualifiers are equal
                        logger.info(f"Equal position values and all equal common qualifiers")
                        add_qualifiers(statement, new_statement, summary=summary)
                        return True
    return False


def add_qualifiers(statement, new_statement, summary=""):
    logger.info(f"Add qualifiers to duplicated item position value")
    # New statement
    # new_statement_claim_property = new_statement.claim.property
    new_statement_claim_id = new_statement.claim.value.id
    #
    add_source = False
    for new_statement_qualifier in new_statement.qualifiers:
        if hasattr(new_statement_qualifier.value, 'id'):
            new_statement_qualifier_value = new_statement_qualifier.value.id
        elif hasattr(new_statement_qualifier.value, 'precision'):
            new_statement_qualifier_value = {'year': new_statement_qualifier.value.year}
            if new_statement_qualifier.value.precision >= 10:
                new_statement_qualifier_value['month'] = new_statement_qualifier.value.month
            if new_statement_qualifier.value.precision >= 11:
                new_statement_qualifier_value['day'] = new_statement_qualifier.value.day
        else:
            new_statement_qualifier_value = new_statement_qualifier.value
        add_qualifier = True
        change_qualifier = False
        for qualifier_pid in statement.qualifiers:
            if new_statement_qualifier.property == qualifier_pid:
                add_qualifier = False
                # for claim in statement.qualifiers[new_statement_qualifier.property]:
                #     if new_statement_qualifier.value.id == claim.target.id:
                #         add_qualifier = False
                for i_claim, claim in enumerate(statement.qualifiers[new_statement_qualifier.property]):
                    if (hasattr(claim.target, 'precision') and
                            claim.target.precision < new_statement_qualifier.value.precision):
                        if ((claim.target.precision == 9 and
                             claim.target.year == new_statement_qualifier.value.year) or
                                (claim.target.precision == 10 and
                                 claim.target.year == new_statement_qualifier.value.year and
                                 claim.target.month == new_statement_qualifier.value.month)):
                            change_qualifier = True
                            i_change_qualifier = i_claim
                            hash_change_qualifier = claim.hash
                        # elif (claim.target.precision == 10 and claim.target.year == new_statement_qualifier.value.year
                        #         and claim.target.month == new_statement_qualifier.value.month):
                        #     edit_qualifier = True
                        #     i_edit_qualifier = i_claim

        if add_qualifier or change_qualifier:
            add_source = True
            if add_qualifier:
                logger.warning(f"Add qualifier ({new_statement_qualifier.property}, "
                               f"{new_statement_qualifier_value}) to already present equal position value "
                               f"{new_statement_claim_id}")  # for item {item.id}")
                # statement._persist_qualifier(new_statement_qualifier, summary=summary)
                statement.addQualifier(new_statement_qualifier._claim, new=True, summary=summary)
                statement.qualifiers[new_statement_qualifier.property].append(new_statement_qualifier._claim)
            elif change_qualifier:
                logger.warning(f"Change qualifier ({new_statement_qualifier.property}, "
                               f"{new_statement_qualifier_value}) to already present equal position value "
                               f"{new_statement_claim_id}")  # for item {item.id}")
                new_statement_qualifier._claim.hash = hash_change_qualifier
                statement.addQualifier(new_statement_qualifier._claim, new=False, summary=summary)
                statement.qualifiers[new_statement_qualifier.property][i_change_qualifier] = \
                    new_statement_qualifier._claim
        else:
            logger.info(f"Skip already present qualifier ({new_statement_qualifier.property}, "
                        f"{new_statement_qualifier_value}) to already present equal position value "
                        f"{new_statement_claim_id}")  # for item {item.id}")
    if add_source:
        new_statement_sources = new_statement.sources
        logger.warning(f"Add source to already present equal position value {new_statement_claim_id}")
        # Check if new source already exists
        for source in statement.sources:
            if IMPORTED_FROM_WIKIMEDIA_PROJECT in source:
                for claim in source[IMPORTED_FROM_WIKIMEDIA_PROJECT]:
                    if claim.target.id == CATALAN_WIKIPEDIA:
                        logger.info(f"Skip adding source because already present")
                        return
        # Add source
        # statement._persist_source(new_statement_source, summary=summary)
        statement.addSources(
            [new_statement_source._claim for new_statement_source in new_statement_sources],
            summary=summary)
        statement.sources.append(
            {new_statement_source.property: new_statement_source._claim
             for new_statement_source in new_statement_sources})
    else:
        logger.info(f"No qualifier added to duplicated item position value")


def remove_positions_from_page(page, infotable_params, summary=""):
    logger.info(f"Remove positions from page: {page}")
    text = page.text
    for param_key, param_value in infotable_params.items():
        param_name, *_ = DIGIT_REGEX.split(param_key)
        # param_num = param_num[0] if param_num else '1'
        if param_name in INFOTABLE_PARAMS:
            text = re.sub(r"\s*\|\s*" + re.escape(param_key) + r"\s*=\s*" + re.escape(param_value) + r"[^|}]*", '',
                          text, count=1, flags=re.MULTILINE)
        # Fix broken-line template
        text = re.sub(r"^\{\{([\w\s']+)\n\}\}", r"{{\1}}", text, count=1, flags=re.MULTILINE)
    page.text = text
    page.save(summary=summary, botflag=True)


class SkipPageError(Exception):
    pass


if __name__ == '__main__':

    # Parse arguments
    args = parse_args()

    # Configurate logger
    config_logger(log_filename=args.log, debug=args.debug)
    logger.info("START transfer_infotable")

    # Generator
    generator = create_generator(groupsize=1)  # TODO: remove groupsize in prod
    for i, page in enumerate(generator):

        IGNORED = [
            "Eleuterio Abad Martín", "Buenaventura Abarzuza Ferrer", "José Abascal Carredano",
            "Abd-Al·lah II de Jordània", "Abdul Hamid I", "Abdul Hamid II", "Abdülâziz",
            "Abdul·lah de l'Aràbia Saudita", "Adolfo de Abel Vilela", "Martí Abella i Pere", "Rosalie Abella",
            "Josep Abelló Padró", "Solvita Āboltiņa", "Hovik Abrahamian",
            # TODO: why?
            "Alcinda Abreu", "Miguel Abriat Cantó", "Santos Abril y Castelló", "Fernando Abril Martorell",
            # 15:
            "Pietro Accolti", "Eduardo Acevedo Maturana" ,"Juan Bautista de Acevedo", "Youssef Achour", "Acoris",
            "Juan Acosta Muñoz", "Gonzalo Acosta Pan", "Octavio Acquaviva", "Antonio Acuña Carballar",
            "Amy Adams (política)", "Adamu", "José María Adán García", "Adelaida II, abadessa de Quedlinburg", "Adimir",
            "Ælfwald d'Ànglia de l'Est",
            # 13:
            "Aelfwine de Deira", "Æthelflæd", "Aethelwold de l'Ànglia Oriental", "Ernesto Agazzi",
            "Pau d'Àger i d'Orcau", "Agim Çeku", "Geraldo Majella Agnelo", "Santiago Agrelo Martínez",
            "Miquel Aguilà i Barril", "Manuel María de Aguilar y Puerta", "Antonio Aguilar y Correa",
            "Salvador Aguilera Carrillo", "Francisco Aguilera y Egea",
            # 16:
            "Enrique de Aguilera y Gamboa", "Lourdes Aguiló Bennàssar", "José Ignacio Aguiló Fuster",
            "José Antonio Aguiriano Forniés", "Pedro Aguirre Cerda", "Francisco Javier Máximo Aguirre de la Hoz",
            "Joaquín Aguirre de la Peña", "Manuel Aguirre de Tejada", "José Ventura Aguirre-Solarte Iturraspe",
            "Miquel d'Agullana", "Bonaventura Agulló i Prats", "Agustí I de Mèxic", "Lorenzo Agustí Pons",
            "Gilberto Agustoni", "Ahazià de Judà", "Ahmed Khatib",
            # 6:
            "Mahmud Ahmadinejad", "Ahmed Aboutaleb", "Ahmet I", "Ahmet II", "Ahmet III",
            "ʻAhoʻeitu ʻUnuakiʻotonga Tukuʻaho",
            # 16: (-36)
            "Antonio Aige Pascual", "Jaume Aiguader i Miró", "Jean-Paul Aimé Gobel",
            "Rafael Aizpún Santafé", "Jesús Aizpún Tuero", "Luis Aizpuru y Mondéjar", "Juan Aizpurúa Azqueta",
            "Juan de Ajuriaguerra Ochandiano", "Baixar al-Àssad", "Hafez al-Àssad", "Mohamed al-Baradei",
            "Mahmud al-Muntasir", "Isidro de Alaix Fábregas", "Cirilo de Alameda y Brea", "Luis Alarcón de la Lastra",
            "Diego de Álava y Esquivel"
        ]
        if page.title() in IGNORED:
            continue

        logger.info(f"Start Page {i + 1}: {page}")
        try:
            infotable_params = parse_infotable(page)
            logger.info(f"Infotable parameters: {infotable_params}")
            if not infotable_params:
                raise SkipPageError
            positions = extract_positions(infotable_params)
            logger.info(f"Positions: {positions}")
            position_statements = create_position_statements(positions)
            if not position_statements:
                raise SkipPageError
            # Get item
            item = get_main_item(page)
            # Add statements
            add_statements(item, position_statements, summary="Import from Catalan Wikipedia")
            # Remove infotable params
            remove_positions_from_page(page, infotable_params, summary="Exporta a Wikidata")
            logger.info(f"End Page: {page}")
        except SkipPageError:
            logger.error(f"Skip Page: no position statements for page {page}")
        # DEBUG
        if args.debug:
            # import pdb;pdb.set_trace()
            if i >= 0:
                break
    logger.info("END transfer_infotable")
