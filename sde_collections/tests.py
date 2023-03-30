from django.test import TestCase

from .sinequa_utils import Sinequa


class CollectionTestCase(TestCase):
    def test_import_sinequa_metadata(self):
        sinequa = Sinequa(config_folder="ARSETAppliedSciences")
        self.assertEqual(
            sinequa.import_treeroot(),
            "Earth Science/Documents/User Guides and Training/ARSET Applied Sciences/",
        )
