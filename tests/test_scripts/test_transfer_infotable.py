"""
python -m pytest -s tests/test_scripts
"""
from collections import OrderedDict

import pytest

from transfer_infotable import extract_positions, get_fixed_electoral_district, get_item_from_page_link, parse_date, \
    parse_position, parse_position_qualifier, parse_position_value

# Constants
# P
APPOINTED_BY = 'P748'
END_TIME = 'P582'
REPLACED_BY = 'P1366'
REPLACES = 'P1365'
SERIES_ORDINAL = 'P1545'
START_TIME = 'P580'
# Q
AMBASSADOR_OF_SPAIN_TO_FRANCE = 'Q27969744'
CITY_COUNCILLOR_OF_SOLSONA = 'Q58219014'
ELECTORAL_DISTRICT = 'P768'
GENERAL_CAPTAIN_OF_VALENCIA = 'Q54875187'
GOVERNOR_OF_HAWAII = 'Q5589655'
IRENE_RIGAU_I_OLIVER = 'Q15743807'
KHEDIVE = 'Q127878'
KING_OF_JORDAN = 'Q14625123'
KING_OF_SAUDI_ARABIA = 'Q850168'
MAYOR_OF_A_CORUNA = 'Q12391919'
MAYOR_OF_LA_VALL_D_UIXO = 'Q26693191'
MAYOR_OF_LUXEMBOURG = 'Q85422522'
MAYOR_OF_REUS = 'Q26698306'
MAYOR_OF_SOLSONA = 'Q26698375'
MAYOR_PRESIDENT_OF_MELILLA = 'Q30727487'
MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN = 'Q18171345'
MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA = 'Q18714088'
MEMBER_OF_THE_PARLIAMENT_OF_GALICIA = 'Q43198218'
MEMBER_OF_THE_SENATE_OF_SPAIN = 'Q19323171'
MEMBER_OF_THE_UNITED_STATES_HOUSE_OF_REPRESENTATIVES = 'Q13218630'
MINISTER_OF_FOREIGN_AFFAIRS_OF_SPAIN = 'Q32969906'
MINISTER_OF_THE_NAVY = 'Q15895305'
PARLIAMENT_OF_CATALONIA = 'Q135630'
PRESIDENT_OF_COLOMBIA = 'Q853475'
PRESIDENT_OF_THE_COUNCIL_OF_CASTILE = 'Q6360109'
PRESIDENT_OF_MALTA = 'Q796593'
PRESIDENT_OF_THE_PALESTINIAN_NATIONAL_AUTHORITY = 'Q2336111'
PRESIDENT_OF_PARAGUAY = 'Q34071'
PRESIDENT_OF_URUGUAY = 'Q4524807'
PRIME_MINISTER_OF_PAKISTAN = 'Q735575'
PRIME_MINISTER_OF_THAILAND = 'Q12376089'
SECRETARY_OF_STATE_OF_SPAIN_DURING_THE_OLD_RULE = 'Q2417901'
SULTAN_OF_MOROCCO = 'Q14566713'
TARRAGONA_CONSTITUENCY_OF_CONGRESS_OF_SPAIN = 'Q7686643'
TARRAGONA_CONSTITUENCY_OF_PARLIAMENT_OF_CATALONIA = 'Q24932383'


class TestScriptTransferInfotable:

    def test_extract_positions(self):
        infotable_params = OrderedDict([
            ('nom', 'Neil Abercrombie'), ('imatge', 'Neil Abercrombie.jpg'), ('1', '250px\n'),
            ('carrec', '7è [[Governador]] de [[Hawaii]]'), ('escut_carrec', 'Seal of the State of Hawaii.svg'),
            ('inici', '{{Data inici|2010|12|6}}'), ('a_etiqueta', 'President'), ('predecessor', '[[Linda Lingle]]'),
            ('carrec2',
             '[[Cambra de Representants dels Estats Units | Membre de la Cambra de Representants dels Estats Units]]'),
            ('escut_carrec2', 'Seal of the United States House of Representatives.svg'),
            ('inici2', '{{Data inici|1991|1|3}}'), ('final2', '{{Data inici|2010|2|28}}'),
            ('predecessor2', '[[Pat Saiki]]'), ('successor2', '[[Charles Djou]]'),
            ('inici3', '{{Data inici|1986|12|20}}'), ('final3', '{{Data inici|1987|1|3}}'),
            ('predecessor3', '[[Cecil Heftel]]'), ('successor3', '[[Pat Saiki]]'),
            ('data_naixement', '{{Data naixement|1938|6|26}}'),
            ('lloc_naixement', '[[Buffalo (Nova York)|Buffalo]], [[Nova York]], {{bandera|EUA}} [[Estats Units]]'),
            ('conjuge', 'Nancie Caraway'), ('partit_politic', '[[Partit Demòcrata dels Estats Units | Demòcrata]]'),
            ('e_etiqueta', 'Vicepresident'), ('ocupacio', 'Assessor de negocis'),
            ('nacionalitat', '{{bandera|EUA}} [[Estatunidenc]]')])
        positions = extract_positions(infotable_params)
        assert isinstance(positions, list)
        assert len(positions) == 3
        assert 'a_etiqueta' in positions[0]
        assert 'predecessor' in positions[0]
        assert positions[0]['predecessor'] == '[[Linda Lingle]]'
        assert 'e_etiqueta' in positions[0]
        assert 'predecessor' in positions[1]
        assert positions[1]['predecessor'] == '[[Pat Saiki]]'
        assert 'predecessor' in positions[2]
        assert positions[2]['predecessor'] == '[[Cecil Heftel]]'
        assert 'carrec' in positions[2]
        assert 'carrec' in positions[1]
        assert positions[2]['carrec'] == positions[1]['carrec']

    @pytest.mark.parametrize("electoral_district, position_value_id, expected_item_id", [
        ("[[província de Tarragona|Tarragona]]", MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA,
         TARRAGONA_CONSTITUENCY_OF_PARLIAMENT_OF_CATALONIA),
        ("Tarragona", MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN, TARRAGONA_CONSTITUENCY_OF_CONGRESS_OF_SPAIN)
    ])
    def test_get_fixed_electoral_district(self, electoral_district, position_value_id, expected_item_id):
        item = get_fixed_electoral_district(electoral_district, position_value_id=position_value_id)
        if item:
            assert item.id == expected_item_id
        else:  # is None
            assert item is expected_item_id

    @pytest.mark.parametrize("link, expected_item_id", [
        ("Irene Rigau i Oliver", IRENE_RIGAU_I_OLIVER),  # from ca.wikipedia
        ("Manuel Casas Fernández", 'Q20535931'),  # from es.wkipedia
        ("Juan González Rodríguez", 'Q12391239'),  # from gl.wikipedia
        ("Rangin Dadfar Spanta", 'Q77348'),  # from en.wikipedia
        ("José Solernou Lapuerta", None),
    ])
    def test_get_item_from_page_link(self, link, expected_item_id):
        item = get_item_from_page_link(link)
        if item:
            assert item.id == expected_item_id
        else:  # is None
            assert item is expected_item_id

    @pytest.mark.parametrize("date, expected_date_claim_value", [
        ("[[23 de gener]] de [[1935]]", {'year': 1935, 'month': 1, 'day': 23}),
        ("[[7 d'agost]] de [[1926]]", {'year': 1926, 'month': 8, 'day': 7}),
        ("[[1918]]", {'year': 1918}),
        ("[[octubre]] de [[1967]]", {'year': 1967, 'month': 10}),
        ("{{Data d'inici i edat|1999|7|5}}", {'year': 1999, 'month': 7, 'day': 5}),
        ("{{Data inici|2000|11|20}}", {'year': 2000, 'month': 11, 'day': 20}),
        ("{{Data inici|2010|3}}", {'year': 2010, 'month': 3}),
        ("{{Data inici|2020}}", {'year': 2020}),
        ("4 d'octubre de 2004", {'year': 2004, 'month': 10, 'day': 4}),
        ("15 gener 2005", {'year': 2005, 'month': 1, 'day': 15}),
        ("''c.'' 810", {'year': 810}),
    ])
    def test_parse_date(self, date, expected_date_claim_value):
        date_claim_value = parse_date(date)
        assert date_claim_value == expected_date_claim_value

    @pytest.mark.parametrize("position, expected_position_claim_id, expected_qualifiers", [
        (OrderedDict([('predecessor', '[[Linda Lingle]]')]), None, []),
    ])
    def test_parse_position(self, position, expected_position_claim_id, expected_qualifiers):
        position_claim, qualifiers = parse_position(position)
        if position_claim:
            assert position_claim.value.id == expected_position_claim_id
        else:
            assert position_claim is expected_position_claim_id
        if qualifiers:
            for claim, (pid, qid) in zip(qualifiers, expected_qualifiers):
                assert claim.property == pid
                assert claim.value.id == qid
        else:
            assert qualifiers == expected_qualifiers

    @pytest.mark.parametrize("key, value, position_value_id, expected_property, expected_value", [
        ("inici", "[[17 de febrer]] de [[2011]]", '', START_TIME, {'year': 2011, 'month': 2, 'day': 17}),
        ("final", "[[17 de febrer]] de [[2011]]", '', END_TIME, {'year': 2011, 'month': 2, 'day': 17}),
        ("predecessor", "[[Irene Rigau i Oliver]]", '', REPLACES, {'id': IRENE_RIGAU_I_OLIVER}),
        ("successor", "[[Irene Rigau i Oliver]]", '', REPLACED_BY, {'id': IRENE_RIGAU_I_OLIVER}),
        ("successor", "-", '', None, {}),
        ("Circumscripció", "[[circumscripció electoral de Barcelona|Barcelona]]", '', ELECTORAL_DISTRICT,
         {'id': 'Q28496610'}),
        ("Proclamació", "[[30 de novembre]] de [[1822]]", '', START_TIME, {'year': 1822, 'month': 11, 'day': 30}),
        ("Circumscripció", "Alacant", '', ELECTORAL_DISTRICT, {'id': 'Q939475'}),
        ("Circumscripció", "[[província de Tarragona|Tarragona]]", MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA,
         ELECTORAL_DISTRICT, {'id': 'Q24932383'}),
    ])
    def test_parse_position_qualifier(self, key, value, position_value_id, expected_property, expected_value):
        qualifier_claim = parse_position_qualifier(key, value, position_value_id=position_value_id)
        qualifier_claim = None if qualifier_claim == 'CONTINUE' else qualifier_claim
        if qualifier_claim:
            assert qualifier_claim.property == expected_property
            for attr, value in expected_value.items():
                assert getattr(qualifier_claim.value, attr, None) == value
        else:  # is None
            assert qualifier_claim is expected_property

    @pytest.mark.parametrize("position_value, expected_position_claim_id, expected_qualifiers", [
        ("[[Ministeri de Marina d'Espanya|Ministre de Marina]]", MINISTER_OF_THE_NAVY, []),
        ("[[La Corunya|Alcalde de La Corunya]]", MAYOR_OF_A_CORUNA, []),
        ("Diputada al [[Parlament de Catalunya]]", MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA, []),
        ("[[Senat d'Espanya|Senadora]] designat pel [[Parlament de Catalunya]]", MEMBER_OF_THE_SENATE_OF_SPAIN, [
            (APPOINTED_BY, PARLIAMENT_OF_CATALONIA)]),
        ("Alcalde de [[la Vall d'Uixó]]", MAYOR_OF_LA_VALL_D_UIXO, []),
        ("[[Llista de presidents de Colòmbia|President de Colòmbia]]", PRESIDENT_OF_COLOMBIA, []),
        ("[[President del Consell de Castella]]", PRESIDENT_OF_THE_COUNCIL_OF_CASTILE, []),
        ("Ambaixador del regne d'Espanya al Regne de França", AMBASSADOR_OF_SPAIN_TO_FRANCE, []),
        ("[[Capità general de València]]", GENERAL_CAPTAIN_OF_VALENCIA, []),
        ("[[Llista dels Ministres d'Afers Exteriors d'Espanya|Ministre d'Estat]]", MINISTER_OF_FOREIGN_AFFAIRS_OF_SPAIN,
         []),
        ("Diputat al [[Congrés dels Diputats]]", MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN, []),
        ("7è [[Governador]] de [[Hawaii]]", GOVERNOR_OF_HAWAII, [(SERIES_ORDINAL, '7')]),
        ("[[Alcalde de Solsona|Alcalde accidental de Solsona]]", MAYOR_OF_SOLSONA, []),
        ("[[Llista d'alcaldes de Reus|Alcalde de Reus]]", MAYOR_OF_REUS, []),
        ("Alcalde-President de Melilla", MAYOR_PRESIDENT_OF_MELILLA, []),
        ("[[Rei de Jordània|Rei]] de [[Jordània]]", KING_OF_JORDAN, []),
        ("Rei de [[Jordània]]", KING_OF_JORDAN, []),
        ("Rei de Jordània", KING_OF_JORDAN, []),
        ("President de l'[[Autoritat Nacional Palestina]]", PRESIDENT_OF_THE_PALESTINIAN_NATIONAL_AUTHORITY, []),
        ("[[Kediv]] d'Egipte i el Sudan", KHEDIVE, []),
        ("Primer Ministre del Pakistan", PRIME_MINISTER_OF_PAKISTAN, []),
        ("Soldà del Marroc", SULTAN_OF_MOROCCO, []),
        ("Diputat al [[Parlament de Galícia]]", MEMBER_OF_THE_PARLIAMENT_OF_GALICIA, []),
        ("President de Malta", PRESIDENT_OF_MALTA, []),
        # ("[[Ajuntament de Solsona|Regidor de l'Ajuntament de Solsona]]", CITY_COUNCILLOR_OF_SOLSONA, []),
        ("[[Llista d'alcaldes de la Ciutat de Luxemburg|Alcalde de la Ciutat de Luxemburg<br/>Primer mandat]]",
         MAYOR_OF_LUXEMBOURG, []),
        ("[[Llista d'alcaldes de la Ciutat de Fake-city|Alcalde de la Ciutat de Fake-city]]", None, []),
        ("[[Cambra de Representants dels Estats Units | Membre de la Cambra de Representants dels Estats Units]]",
         MEMBER_OF_THE_UNITED_STATES_HOUSE_OF_REPRESENTATIVES, []),
        ("[[Secretari d'Estat (Monarquia Absolutista borbònica)|Secretari d'Estat]]",
         SECRETARY_OF_STATE_OF_SPAIN_DURING_THE_OLD_RULE, []),
        ("1r [[Reis de l'Aràbia Saudita|rei]] de l'[[Aràbia Saudita]]", KING_OF_SAUDI_ARABIA, [(SERIES_ORDINAL, '1')]),
        ("[[Primer ministre de Tailàndia]]", PRIME_MINISTER_OF_THAILAND, []),
        ("[[Llista de presidents del Paraguai|President del Paraguai]]", PRESIDENT_OF_PARAGUAY, []),
        ("[[President de l'Uruguai]]", PRESIDENT_OF_URUGUAY, []),
    ])
    def test_parse_position_value(self, position_value, expected_position_claim_id, expected_qualifiers):
        position_claim, qualifiers = parse_position_value(position_value)
        if position_claim:
            assert position_claim.value.id == expected_position_claim_id
        else:
            assert position_claim is expected_position_claim_id
        if qualifiers:
            for claim, (pid, value) in zip(qualifiers, expected_qualifiers):
                assert claim.property == pid
                if isinstance(claim.value, str):
                    assert claim.value == value
                else:
                    qid = value
                    assert claim.value.id == qid
        else:
            assert qualifiers == expected_qualifiers

