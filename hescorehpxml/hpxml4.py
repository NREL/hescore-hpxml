from .hpxml3 import HPXML3toHEScoreTranslator


class HPXML4toHEScoreTranslator(HPXML3toHEScoreTranslator):
    SCHEMA_DIR = 'hpxml-4.0.0'

    def get_attic_floors(self, attic):
        floor_idref = self.xpath(attic, 'h:AttachedToFloor/@idref', aslist=True)
        # No frame floor attached
        if not floor_idref:
            return []
        b = self.xpath(attic, 'ancestor::h:Building')
        floors = self.xpath(b, '//h:Floor[contains("{}",h:SystemIdentifier/@id)]'.format(floor_idref),
                                    aslist=True, raise_err=True)

        return floors