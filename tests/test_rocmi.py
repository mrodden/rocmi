from pyfakefs.fake_filesystem_unittest import TestCase

from tests.test_kfd import setup_cards


def get_sample_pci_id_content():
    # subset of data from hwdata pci.ids
    return b"""
1002  Advanced Micro Devices, Inc. [AMD/ATI]
        1114  Krackan [Radeon 840M / 860M Graphics]
        1304  Kaveri
        7388  Arcturus GL-XL
        738c  Arcturus GL-XL [Instinct MI100]
        738e  Arcturus GL-XL [Instinct MI100]
        74a0  Aqua Vanjaram [Instinct MI300A]
        74a1  Aqua Vanjaram [Instinct MI300X]
        74a2  Aqua Vanjaram [Instinct MI308X]
        74a5  Aqua Vanjaram [Instinct MI325X]
        74a9  Aqua Vanjaram [Instinct MI300X HF]
        74b5  Aqua Vanjaram [Instinct MI300X VF]
        74b9  Aqua Vanjaram [Instinct MI325X VF]
        74bd  Aqua Vanjaram [Instinct MI300X HF]
        7550  Navi 48 [Radeon RX 9070/9070 XT/9070 GRE]
                148c 2435  Reaper Radeon RX 9070 XT 16GB GDDR6 (RX9070XT 16G-A)
                1da2 e490  Navi 48 XTX [Sapphire Pulse Radeon RX 9070 XT]
        7590  Navi 44 [Radeon RX 9060 XT]
"""


class RocmiTestCase(TestCase):

    def setUp(self):
        self.setUpPyfakefs()

        # rocmi scans hardware on import, so we have to stub the kfd stuff too
        setup_cards(self.fs)

        # have to import after patching filesystem
        global rocmi
        import rocmi

    def test_search_pci_ids_fedora(self):
        self.fs.create_file(
            "/usr/share/hwdata/pci.ids", contents=get_sample_pci_id_content()
        )

        name = rocmi.search_pci_ids("738c")
        self.assertEqual(name, "Arcturus GL-XL [Instinct MI100]")

    def test_search_pci_ids_debian(self):
        self.fs.create_file(
            "/usr/share/misc/pci.ids", contents=get_sample_pci_id_content()
        )

        name = rocmi.search_pci_ids("738c")
        self.assertEqual(name, "Arcturus GL-XL [Instinct MI100]")

    def test_search_pci_ids_no_file(self):
        name = rocmi.search_pci_ids("738c")
        self.assertIsNone(name)
