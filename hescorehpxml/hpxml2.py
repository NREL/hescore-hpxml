from .base import HPXMLtoHEScoreTranslatorBase
from .exceptions import TranslationError


def convert_to_type(type_, value):
    if value is None:
        return value
    else:
        return type_(value)


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

    def get_foundation_walls(self, fnd, v3_b):
        foundationwalls = self.xpath(fnd, 'h:FoundationWall', aslist=True)
        return foundationwalls

    def get_foundation_slabs(self, fnd, v3_b):
        slabs = self.xpath(fnd, 'h:Slab', raise_err=True, aslist=True)
        return slabs

    def get_foundation_frame_floors(self, fnd, v3_b):
        frame_floors = self.xpath(fnd, 'h:FrameFloor', aslist=True)
        return frame_floors

    def attic_has_rigid_sheathing(self, attic, v3_roof):
        return self.xpath(attic,
                          'boolean(h:AtticRoofInsulation/h:Layer[h:NominalRValue > 0][h:InstallationType="continuous"][boolean(h:InsulationMaterial/h:Rigid)])'  # noqa: E501
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
            knee_walls.append(wall)

        return knee_walls

    def get_attic_type(self, attic, atticid):
        hpxml_attic_type = self.xpath(attic, 'h:AtticType/text()')
        rooftypemap = {'cape cod': 'cath_ceiling',
                       'cathedral ceiling': 'cath_ceiling',
                       'flat roof': 'cath_ceiling',
                       'unvented attic': 'vented_attic',
                       'vented attic': 'vented_attic',
                       'venting unknown attic': 'vented_attic',
                       'other': None}

        if rooftypemap[hpxml_attic_type] is None:
            attc_is_cond = self.xpath(attic, 'h:extension/h:Conditioned/text()')
            if attc_is_cond == 'true':
                return 'cond_attic'
            else:
                raise TranslationError(
                    'Attic {}: Cannot translate HPXML AtticType {} to HEScore rooftype.'.format(atticid,
                                                                                                hpxml_attic_type))
        return rooftypemap[hpxml_attic_type]

    def get_attic_floor_rvalue(self, attic, v3_b):
        return self.xpath(attic, 'sum(h:AtticFloorInsulation/h:Layer/h:NominalRValue)')

    def get_attic_area(self, attic, is_one_roof, footprint_area, v3_roofs, v3_b):
        attic_area = convert_to_type(float, self.xpath(attic, 'h:Area/text()'))
        if attic_area is None:
            if is_one_roof:
                attic_area = footprint_area
            else:
                raise TranslationError(
                    'If there are more than one Attic elements, each needs an area. Please specify under Attic/Area.')
        return attic_area

    def get_attic_roof_area(self, roof):
        return self.xpath(roof, 'h:RoofArea/text()')

    def get_sunscreen(self, wndw_skylight):
        return bool(self.xpath(wndw_skylight, 'h:Treatments/text()') == 'solar screen'
                    or self.xpath(wndw_skylight, 'h:ExteriorShading/text()') == 'solar screens')

    def get_hescore_walls(self, b):
        return self.xpath(b,
                          'h:BuildingDetails/h:Enclosure/h:Walls/h:Wall[h:ExteriorAdjacentTo="ambient" or not(h:ExteriorAdjacentTo)]',  # noqa: E501
                          aslist=True)

    def check_is_doublepane(self, v3_window, glass_layers):
        return glass_layers in ('double-pane', 'single-paned with storms', 'single-paned with low-e storms')

    def check_is_storm_lowe(self, window, glass_layers):
        return glass_layers == 'single-paned with low-e storms'

    def get_duct_location(self, hpxml_duct_location, v3_bldg):
        return self.duct_location_map[hpxml_duct_location]

    duct_location_map = {'conditioned space': 'cond_space',
                         'unconditioned space': None,
                         'unconditioned basement': 'uncond_basement',
                         'unvented crawlspace': 'unvented_crawl',
                         'vented crawlspace': 'vented_crawl',
                         'crawlspace': None,
                         'unconditioned attic': 'uncond_attic',
                         'interstitial space': None,
                         'garage': 'vented_crawl',
                         'outside': None}
