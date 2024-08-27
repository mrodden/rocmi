from pyfakefs.fake_filesystem_unittest import TestCase


def setup_cards(fs):
    fs.create_dir("/sys/class/kfd/kfd/topology/nodes")

    gpu_id = b"42700"
    name = b"arcturus"
    properties = b"""cpu_cores_count 0
simd_count 480
mem_banks_count 1
caches_count 217
io_links_count 1
p2p_links_count 3
cpu_core_id_base 0
simd_id_base 2147487744
max_waves_per_simd 10
lds_size_in_kb 64
gds_size_in_kb 0
num_gws 64
wave_front_size 64
array_count 8
simd_arrays_per_engine 1
cu_per_simd_array 16
simd_per_cu 4
max_slots_scratch_cu 32
gfx_target_version 90008
vendor_id 4098
device_id 29580
location_id 8960
domain 0
drm_render_minor 128
hive_id 0
num_sdma_engines 2
num_sdma_xgmi_engines 6
num_sdma_queues_per_engine 8
num_cp_queues 24
max_engine_clk_fcompute 1502
local_mem_size 0
fw_version 65
capability 749970048
debug_prop 1494
sdma_fw_version 18
unique_id 7809984429061111111
num_xcc 1
max_engine_clk_ccompute 2000
"""

    fs.create_file("/sys/class/kfd/kfd/topology/nodes/0/gpu_id", contents=gpu_id)
    fs.create_file("/sys/class/kfd/kfd/topology/nodes/0/name", contents=name)
    fs.create_file(
        "/sys/class/kfd/kfd/topology/nodes/0/properties", contents=properties
    )


class KFDTestCase(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        setup_cards(self.fs)

        # have to import after patching filesystem
        global kfd
        from rocmi import kfd

    def test_get_processes_no_allocs(self):
        """Verify get_processes works with a PID without any GPU memory reserved."""

        self.fs.create_file("/proc/4444/comm", contents=b"test-process")
        self.fs.create_file("/sys/class/kfd/kfd/proc/4444/pasid", contents=b"1234")
        self.fs.create_dir("/sys/class/kfd/kfd/proc/4444/queues")

        for p in kfd.get_processes():
            self.assertEqual(p.name, "test-process")
            self.assertEqual(p.pasid, 1234)

    def test_iter_kfd_nodes_count(self):
        devs = kfd._iter_kfd_devices()
        self.assertEqual(len(devs), 1)
