from .base import HPXMLtoHEScoreTranslatorBase
from collections import OrderedDict
from .exceptions import (
    TranslationError,
    ElementNotFoundError,
    InputOutOfBounds,
    RoundOutOfBounds,
)

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
            return max([self.xpath(b, 'sum(descendant::h:%s[contains(%s, h:SystemIdentifier/@id)]/h:Area)' % (key, value)) for key, value in attached_ids.items()])

        fnd.sort(key=get_fnd_area, reverse=True)
        return fnd, get_fnd_area

    def get_foundation_walls(self, fnd, ns, b):
        attached_ids = self.xpath(fnd, 'h:AttachedToFoundationWall/@idref')
        foundationwalls = b.xpath('descendant::h:FoundationWall[contains(%s, h:SystemIdentifier/@id)]' % attached_ids, namespaces=ns)
        return foundationwalls

    def get_foundation_slabs(self, fnd, b):
        attached_ids = self.xpath(fnd, 'h:AttachedToFoundationWall/@idref')
        slabs = self.xpath(b, 'descendant::h:Slab[contains(%s, h:SystemIdentifier/@id)]' % attached_ids, raise_err=True, aslist=True)
        return slabs

    def get_foundation_frame_floors(self, fnd, ns, b):
        attached_ids = self.xpath(fnd, 'h:AttachedToFrameFloor/@idref')
        frame_floors = b.xpath('descendant::h:FrameFloor[contains(%s, h:SystemIdentifier/@id)]' % attached_ids, namespaces=ns)
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
                                'descendant::h:Wall[h:SystemIdentifier/@id=$kneewallid]',
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

    def get_attic_floor_rvalue(self, attic, b):
        floor_idref = self.xpath(attic, 'h:AttachedToFrameFloor/@idref')
        frame_floor = b.xpath('descendant::h:FrameFloor[contains(%s, h:SystemIdentifier/@id)]' % floor_idref)
        return self.xpath(frame_floor, 'sum(h:Insulation/h:Layer/h:NominalRValue)')