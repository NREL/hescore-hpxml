import io
from lxml import objectify
import pathlib
import pytest
import re

from hescorehpxml import HPXMLtoHEScoreTranslator

both_hescore_min = [
    'hescore_min_v3',
    'hescore_min'
]


def get_example_xml_tree_elementmaker(filebase):
    rootdir = pathlib.Path(__file__).resolve().parent.parent
    hpxmlfilename = str(rootdir / 'examples' / f'{filebase}.xml')
    tree = objectify.parse(hpxmlfilename)
    root = tree.getroot()
    ns = re.match(r'\{(.+)\}', root.tag).group(1)
    E = objectify.ElementMaker(
        annotate=False,
        namespace=ns
    )
    return tree, E


def scrub_hpxml_doc(doc):
    f_in = io.BytesIO()
    doc.write(f_in)
    f_in.seek(0)
    tr = HPXMLtoHEScoreTranslator(f_in)
    f_out = io.BytesIO()
    tr.export_scrubbed_hpxml(f_out)
    f_out.seek(0)
    scrubbed_doc = objectify.parse(f_out)
    return scrubbed_doc


@pytest.mark.parametrize('hpxml_filebase', both_hescore_min)
def test_remove_customer(hpxml_filebase):
    doc, E = get_example_xml_tree_elementmaker(hpxml_filebase)
    hpxml = doc.getroot()
    hpxml.Building.addprevious(
        E.Customer(
            E.CustomerDetails(
                E.Person(
                    E.SystemIdentifier(
                        E.SendingSystemIdentifierType('some other id'),
                        E.SendingSystemIdentifierValue('1234'),
                        id='customer1'
                    ),
                    E.Name(
                        E.FirstName('John'),
                        E.LastName('Doe')
                    ),
                    E.Telephone(
                        E.TelephoneNumber('555-555-5555')
                    )
                ),
                E.MailingAddress(
                    E.Address1('PO Box 1234'),
                    E.CityMunicipality('Anywhere'),
                    E.StateCode('CO')
                )
            )
        )
    )
    doc2 = scrub_hpxml_doc(doc)
    hpxml2 = doc2.getroot()
    assert len(hpxml2.Customer) == 1
    assert len(hpxml2.Customer.getchildren()) == 1
    assert len(hpxml2.Customer.CustomerDetails.getchildren()) == 1
    assert len(hpxml2.Customer.CustomerDetails.Person.getchildren()) == 1
    assert hpxml2.Customer.CustomerDetails.Person.SystemIdentifier.attrib['id'] == 'customer1'


@pytest.mark.parametrize('hpxml_filebase', both_hescore_min)
def test_remove_health_and_safety(hpxml_filebase):
    doc, E = get_example_xml_tree_elementmaker(hpxml_filebase)
    hpxml = doc.getroot()
    hpxml.Building.BuildingDetails.Systems.addnext(
        E.HealthAndSafety()
    )
    doc2 = scrub_hpxml_doc(doc)
    assert len(doc2.xpath('//h:HealthAndSafety', namespaces={'h': hpxml.nsmap[None]})) == 0
