from .base import HPXMLtoHEScoreTranslatorBase
from .exceptions import (
    TranslationError,
    ElementNotFoundError,
    InputOutOfBounds,
    RoundOutOfBounds,
)

class HPXML2toHEScoreTranslator(HPXMLtoHEScoreTranslatorBase):

    SCHEMA_DIR = 'hpxml-2.3.0'

    def check_hpwes(self, p, v3_b):
        if p is not None:
            return self.xpath(p, 'h:ProjectDetails/h:ProgramCertificate="Home Performance with Energy Star"')

    def sort_foundations(self, fnd, v3_b):
    # Sort the foundations from largest area to smallest
        def get_fnd_area(fnd):
            return max([self.xpath(fnd, 'sum(h:%s/h:Area)' % x) for x in ('Slab', 'FrameFloor')])

        fnd.sort(key=get_fnd_area, reverse=True)
        return fnd, get_fnd_area

    def get_foundation_walls(self, fnd, ns, v3_b):
        foundationwalls = fnd.xpath('h:FoundationWall', namespaces=ns)
        return foundationwalls

    def get_foundation_slabs(self, fnd, v3_b):
        slabs = self.xpath(fnd, 'h:Slab', raise_err=True, aslist=True)
        return slabs

    def get_foundation_frame_floors(self, fnd, ns, v3_b):
        frame_floors = fnd.xpath('h:FrameFloor', namespaces=ns)
        return frame_floors

    def attic_has_rigid_sheathing(self, attic, v3_roof):
        return self.xpath(attic,
                          'boolean(h:AtticRoofInsulation/h:Layer[h:NominalRValue > 0][h:InstallationType="continuous"][boolean(h:InsulationMaterial/h:Rigid)])'
                          # noqa: E501
                          )

    def get_attic_roof_rvalue(self, attic, v3_roof):
        return self.xpath(attic,
                          'sum(h:AtticRoofInsulation/h:Layer/h:NominalRValue)')

    def get_attic_knee_walls(self, attic, b):
        knee_walls = []
        for kneewall_idref in self.xpath(attic, 'h:AtticKneeWall/@idref', aslist=True):
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

    def get_attic_floor_rvalue(self, attic, v3_b):
        return self.xpath(attic, 'sum(h:AtticFloorInsulation/h:Layer/h:NominalRValue)')