from .base import HPXMLtoHEScoreTranslatorBase
from collections import OrderedDict
from .exceptions import (
    TranslationError,
    ElementNotFoundError,
    InputOutOfBounds,
    RoundOutOfBounds,
)

def convert_to_type(type_, value):
    if value is None:
        return value
    else:
        return type_(value)

class HPXML3toHEScoreTranslator(HPXMLtoHEScoreTranslatorBase):

    SCHEMA_DIR = 'hpxml-3.0.0'

    def check_hpwes(self, v2_p, b):
        # multiple verification nodes?
        return self.xpath(b, 'h:BuildingDetails/h:GreenBuildingVerifications/h:GreenBuildingVerification/h:Type="Home Performance with ENERGY STAR"')

    def sort_foundations(self, fnd, b):
        # Sort the foundations from largest area to smallest
        def get_fnd_area(fnd):
            attached_ids = OrderedDict()
            attached_ids['Slab'] = self.xpath(fnd, 'h:AttachedToSlab/@idref')
            attached_ids['FrameFloor'] = self.xpath(fnd, 'h:AttachedToFrameFloor/@idref')
            return max([self.xpath(b, 'sum(//h:%s[contains(%s, h:SystemIdentifier/@id)]/h:Area)' % (key, value)) for key, value in attached_ids.items()])

        fnd.sort(key=get_fnd_area, reverse=True)
        return fnd, get_fnd_area

    def get_foundation_walls(self, fnd, b):
        attached_ids = self.xpath(fnd, 'h:AttachedToFoundationWall/@idref')
        foundationwalls = self.xpath(b, '//h:FoundationWall[contains(%s, h:SystemIdentifier/@id)]' % attached_ids, aslist=True)
        return foundationwalls

    def get_foundation_slabs(self, fnd, b):
        attached_ids = self.xpath(fnd, 'h:AttachedToFoundationWall/@idref')
        slabs = self.xpath(b, '//h:Slab[contains(%s, h:SystemIdentifier/@id)]' % attached_ids, raise_err=True, aslist=True)
        return slabs

    def get_foundation_frame_floors(self, fnd, b):
        attached_ids = self.xpath(fnd, 'h:AttachedToFrameFloor/@idref')
        frame_floors = self.xpath(b, '//h:FrameFloor[contains(%s, h:SystemIdentifier/@id)]' % attached_ids, aslist=True)
        return frame_floors

    def attic_has_rigid_sheathing(self, v2_attic, roof):
        return self.xpath(roof,
                          'boolean(h:Insulation/h:Layer[h:NominalRValue > 0][h:InstallationType="continuous"][boolean(h:InsulationMaterial/h:Rigid)])'
                          # noqa: E501
                          )

    def get_attic_roof_rvalue(self, v2_attic, roof):
        return self.xpath(roof,
                          'sum(h:Insulation/h:Layer/h:NominalRValue)')

    def get_attic_knee_walls(self, attic, b):
        knee_walls = []
        for kneewall_idref in self.xpath(attic, 'h:AttachedToWall/@idref', aslist=True):
            wall = self.xpath(
                                b,
                                '//h:Wall[h:SystemIdentifier/@id=$kneewallid][h:AtticWallType="knee wall"]',
                                raise_err=True,
                                kneewallid=kneewall_idref
            )
            wall_rvalue = self.xpath(wall, 'sum(h:Insulation/h:Layer/h:NominalRValue)')
            wall_area = self.xpath(wall, 'h:Area/text()')
            if wall_area is None:
                raise TranslationError('All attic knee walls need an Area specified')
            wall_area = float(wall_area)
            knee_walls.append({'area': wall_area, 'rvalue': wall_rvalue})

        return knee_walls

    def get_attic_type(self, attic, atticd, atticid):
        if self.xpath(attic, 'h:AtticType/h:Attic/h:CapeCod or boolean(h:AtticType/h:FlatRoof) or boolean(h:AtticType/h:CathedralCeiling)'):
            atticd['rooftype'] = 'cath_ceiling'
        elif self.xpath(attic, 'boolean(h:AtticType/h:Attic/h:Vented)'):
            atticd['rooftype'] = 'vented_attic'
        elif self.xpath(attic, 'boolean(h:AtticType/h:Attic/h:Conditioned)'):
            atticd['rooftype'] = 'cond_attic'
        else:
            raise TranslationError(
                'Attic {}: Cannot translate HPXML AtticType to HEScore rooftype.'.format(atticid))

    def get_attic_floor_rvalue(self, attic, b):
        floor_idref = self.xpath(attic, 'h:AttachedToFrameFloor/@idref')
        frame_floors = self.xpath(b, '//h:FrameFloor[contains(%s, h:SystemIdentifier/@id)]' % floor_idref, aslist=True)
        rvalue = 0.0
        for frame_floor in frame_floors:
            rvalue += self.xpath(frame_floor, 'sum(h:Insulation/h:Layer/h:NominalRValue)')
        return rvalue

    def get_roof_area(self, attic, b):
        floor_idref = self.xpath(attic, 'h:AttachedToFrameFloor/@idref')
        frame_floors = self.xpath(b, '//h:FrameFloor[contains("%s", h:SystemIdentifier/@id)]' % floor_idref, aslist=True)
        area = 0.0
        for frame_floor in frame_floors:
            area += convert_to_type(float, self.xpath(frame_floor, 'h:Area/text()'))
        return area

    def get_sunscreen(self, wndw_skylight):
        return bool(self.xpath(wndw_skylight, 'h:ExteriorShading/h:Type/text()') == 'solar screens')

    def get_hescore_walls(self, b):
        return self.xpath(b,
            'h:BuildingDetails/h:Enclosure/h:Walls/h:Wall[h:ExteriorAdjacentTo="outside" or not(h:ExteriorAdjacentTo)]', aslist=True)

    duct_location_map = {'living space': 'cond_space',
                         'unconditioned space': None,
                         'basement': None, # Fix me
                         'basement - unconditioned': 'uncond_basement',
                         'basement - conditioned': 'cond_space', # Fix me
                         'crawlspace - unvented': 'unvented_crawl',
                         'crawlspace - vented': 'vented_crawl',
                         'crawlspace - unconditioned': None, # Fix me
                         'crawlspace - conditioned': None, # Fix me
                         'crawlspace': None,
                         'unconditioned attic': 'uncond_attic',
                         'interstitial space': None,
                         'garage - conditioned': None, # Fix me
                         'garage - unconditioned': None, # Fix me
                         'garage': 'vented_crawl',
                         'roof deck': None, # Fix me
                         'outside': None,
                         'attic': None, # Fix me
                         'attic - unconditioned': None, # Fix me
                         'attic - conditioned': None, # Fix me
                         'attic - unvented': None, # Fix me
                         'attic - vented': None } # Fix me