from .hpxml3 import HPXML3toHEScoreTranslator


class HPXML4toHEScoreTranslator(HPXML3toHEScoreTranslator):
    SCHEMA_DIR = 'hpxml-4.0.0'

    # TODO: Identify the differences with v3 and implement here.
