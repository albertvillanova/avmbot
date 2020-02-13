"""
python -m pytest -s tests/test_scripts
"""
from collections import OrderedDict

import pytest

from transfer_infotable import extract_positions, parse_date, parse_position, parse_position_qualifier, parse_position_value

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
GENERAL_CAPTAIN_OF_VALENCIA = 'Q54875187'
GOVERNOR_OF_HAWAII = 'Q5589655'
MAYOR_OF_A_CORUNA = 'Q12391919'
MAYOR_OF_LA_VALL_D_UIXO = 'Q26693191'
MEMBER_OF_THE_CONGRESS_OF_DEPUTIES_OF_SPAIN = 'Q18171345'
MEMBER_OF_THE_PARLIAMENT_OF_CATALONIA = 'Q18714088'
MEMBER_OF_THE_SENATE_OF_SPAIN = 'Q19323171'
MINISTER_OF_FOREIGN_AFFAIRS_OF_SPAIN = 'Q32969906'
MINISTER_OF_THE_NAVY = 'Q15895305'
PARLIAMENT_OF_CATALONIA = 'Q135630'
PRESIDENT_OF_COLOMBIA = 'Q853475'
PRESIDENT_OF_THE_COUNCIL_OF_CASTILE = 'Q6360109'


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
        # # TODO
        # assert 'e_etiqueta' in positions[0]
        # assert 'predecessor' in positions[1]
        # assert positions[1]['predecessor'] == '[[Pat Saiki]]'
        # assert 'predecessor' in positions[2]
        # assert positions[2]['predecessor'] == '[[Cecil Heftel]]'
        # # TODO
        # assert 'carrec' in positions[2]
        # assert 'carrec' in positions[1]
        # assert positions[2]['carrec'] == positions[1]['carrec']

    @pytest.mark.parametrize("date, expected_date_claim_value", [
        ("[[23 de gener]] de [[1935]]", {'year': 1935, 'month': 1, 'day': 23}),
        ("[[7 d'agost]] de [[1926]]", {'year': 1926, 'month': 8, 'day': 7}),
        ("[[1918]]", {'year': 1918}),
        ("[[octubre]] de [[1967]]", {'year': 1967, 'month': 10}),
        ("{{Data d'inici i edat|1999|7|5}}", {'year': 1999, 'month': 7, 'day': 5}),
        ("{{Data inici|2000|11|20}}", {'year': 2000, 'month': 11, 'day': 20}),
        ("{{Data inici|2010|3}}", {'year': 2010, 'month': 3}),
        ("{{Data inici|2020}}", {'year': 2020}),
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

    @pytest.mark.parametrize("key, value, expected_property, expected_value", [
        ("inici", "[[17 de febrer]] de [[2011]]", START_TIME, {'year': 2011, 'month': 2, 'day': 17}),
        ("final", "[[17 de febrer]] de [[2011]]", END_TIME, {'year': 2011, 'month': 2, 'day': 17}),
        ("predecessor", "[[Irene Rigau i Oliver]]", REPLACES, {'id': 'Q15743807'}),
        ("successor", "[[Irene Rigau i Oliver]]", REPLACED_BY, {'id': 'Q15743807'}),
        ("successor", "-", None, {}),
    ])
    def test_parse_position_qualifier(self, key, value, expected_property, expected_value):
        qualifier_claim = parse_position_qualifier(key, value)
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

