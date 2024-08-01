#!/usr/bin/env python3

# Copyright 2024 Mathew Odden <mathewrodden@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from collections import namedtuple
import ctypes
from ctypes import c_uint8, c_uint16, c_uint32, c_uint64
import logging
import os
import sys
import re
import struct


LOG = logging.getLogger(__name__)

u8 = c_uint8
u16 = c_uint16
u32 = c_uint32
u64 = c_uint64


AMD_GPU_ID = 0x1002


class MetricsHeader(ctypes.Structure):
    _fields_ = [
        ("structure_size", u16),
        ("format_revision", u8),
        ("content_revision", u8),
    ]


RSMI_NUM_HBM_INSTANCES = 4
RSMI_MAX_NUM_VCNS = 4
RSMI_MAX_NUM_XGMI_LINKS = 8
RSMI_MAX_NUM_GFX_CLKS = 8
RSMI_MAX_NUM_CLKS = 4
RSMI_MAX_NUM_JPEG_ENGS = 32


class Metrics_1_5(ctypes.Structure):
    _fields_ = [
        ("metrics_header", MetricsHeader),
        ("temperature_hotspot", u16),
        ("temperature_mem", u16),
        ("temperature_vrsoc", u16),
        ("current_socket_power", u16),
        ("average_gfx_activity", c_uint16),
        ("average_umc_activity", c_uint16),
        ("vcn_activity", u16 * RSMI_MAX_NUM_VCNS),
        ("jpeg_activity", u16 * RSMI_MAX_NUM_JPEG_ENGS),
        ("energy_accumulator", c_uint64),
        ("system_clock_counter", c_uint64),
        ("throttle_status", c_uint32),
        ("gfxclk_lock_status", u32),
        ("pcie_link_width", c_uint16),
        ("pcie_link_speed", c_uint16),
        ("xgmi_link_width", u16),
        ("xgmi_link_speed", u16),
        ("gfx_activity_acc", c_uint32),
        ("mem_activity_acc", c_uint32),
        ("pcie_bandwidth_acc", u64),
        ("pcie_bandwidth_inst", u64),
        ("pcie_l0_to_recov_count_acc", u64),
        ("pcie_replay_count_acc", u64),
        ("pcie_replay_rover_count_acc", u64),
        ("pcie_nak_sent_count_acc", u32),
        ("pcie_nak_rcvd_count_acc", u32),
        ("xgmi_read_data_acc", u64 * RSMI_MAX_NUM_XGMI_LINKS),
        ("xgmi_write_data_acc", u64 * RSMI_MAX_NUM_XGMI_LINKS),
        ("firmware_timestamp", c_uint64),
        ("current_gfxclks", c_uint16 * RSMI_MAX_NUM_GFX_CLKS),
        ("current_socclks", c_uint16 * RSMI_MAX_NUM_CLKS),
        ("current_vclk0s", c_uint16 * RSMI_MAX_NUM_CLKS),
        ("current_dclk0s", c_uint16 * RSMI_MAX_NUM_CLKS),
        ("current_uclk", c_uint16),
        ("_padding", c_uint16),
    ]


class Metrics_1_3(ctypes.Structure):
    _fields_ = [
        ("metrics_header", MetricsHeader),
        ("temperature_edge", u16),
        ("temperature_hotspot", u16),
        ("temperature_mem", u16),
        ("temperature_vrgfx", u16),
        ("temperature_vrsoc", u16),
        ("temperature_vrmem", u16),
        ("average_gfx_activity", c_uint16),
        ("average_umc_activity", c_uint16),
        ("average_mm_activity", c_uint16),
        ("average_socket_power", c_uint16),
        ("energy_accumulator", c_uint64),
        ("system_clock_counter", c_uint64),
        ("average_gfxclk_frequency", c_uint16),
        ("average_socclk_frequency", c_uint16),
        ("average_uclk_frequency", c_uint16),
        ("average_vclk0_frequency", c_uint16),
        ("average_dclk0_frequency", c_uint16),
        ("average_vclk1_frequency", c_uint16),
        ("average_dclk1_frequency", c_uint16),
        ("current_gfxclk", c_uint16),
        ("current_socclk", c_uint16),
        ("current_uclk", c_uint16),
        ("current_vclk0", c_uint16),
        ("current_dclk0", c_uint16),
        ("current_vclk1", c_uint16),
        ("current_dclk1", c_uint16),
        ("throttle_status", c_uint32),
        ("current_fan_speed", c_uint16),
        ("pcie_link_width", c_uint16),
        ("pcie_link_speed", c_uint16),
        ("_padding", c_uint16),
        ("gfx_activity_acc", c_uint32),
        ("mem_activity_acc", c_uint32),
        ("temperature_hbm", c_uint16 * RSMI_NUM_HBM_INSTANCES),
        ("firmware_timestamp", c_uint64),
        ("voltage_soc", c_uint16),
        ("voltage_gfx", c_uint16),
        ("voltage_mem", c_uint16),
        ("_padding1", c_uint16),
        ("indep_throttle_status", c_uint64),
    ]


def print_struct(s):
    for f, t in s._fields_:
        print("%s=%r" % (f, getattr(s, f)))


def iter_devices():

    devices = []

    cards = []

    for root, dirs, files in os.walk("/sys/class/drm"):
        for d in dirs:
            if d.startswith("card"):
                cards.append(d)

    for card in cards:
        path = "/sys/class/drm/%s/device/vendor" % card
        try:
            vend = open(path, "rb").read().strip()
            vend = int(vend, 16)
        except Exception:
            LOG.debug("error reading vendor from %s" % path)
            continue

        if vend == AMD_GPU_ID:
            devices.append(card)

    return devices


def search_pci_ids(device_id):
    with open("/usr/share/misc/pci.ids") as fd:
        lines = fd.read().split("\n")

    for l in lines:
        if l.startswith("#"):
            continue

        parts = l.strip().split("  ", 1)
        if len(parts) < 2:
            continue

        try:
            id, name = parts
        except Exception:
            continue

        if device_id == id:
            return name.strip()


def read_clocks(path):

    with open(path, "r") as fd:
        dat = fd.read()

    clocks = []
    for line in dat.split("\n"):
        pat = re.compile("\d: ([\d]+)[\w]+")
        match = pat.search(line)
        if match:
            clocks.append(int(match.group(1)))

    return clocks


ComputeProcess = namedtuple(
    "ComputeProcess",
    [
        "pid",
        "pasid",
    ],
)


def get_processes():
    parent = "/sys/class/kfd/kfd/proc"
    procs = []
    for proc_dir in os.listdir(parent):

        try:
            pid = int(proc_dir)
        except Exception:
            continue

        with open(os.path.join(parent, proc_dir, "pasid")) as fd:
            pasid = int(fd.read().strip())

        procs.append(ComputeProcess(pid=pid, pasid=pasid))

    return procs


# cat /proc/3766769/fdinfo/8
fdinfo_sample = """
pos:    0
flags:  02100002
mnt_id: 1873
ino:    19
pasid:  32771
drm-driver:     amdgpu
drm-pdev:       0000:83:00.0
drm-client-id:  1203108
drm-memory-vram:        76 KiB
drm-memory-gtt:         44 KiB
drm-memory-cpu:         6200 KiB
amd-memory-visible-vram:        76 KiB
amd-evicted-vram:       0 KiB
amd-evicted-visible-vram:       0 KiB
amd-requested-vram:     76 KiB
amd-requested-visible-vram:     76 KiB
amd-requested-gtt:      56 KiB
"""


def read_process_fdinfos():
    pass


class PowerDescriptorMixin:
    def _hwmon_data(self, file_name):
        hwmon_dir = next(iter(os.listdir(os.path.join(self.path, "hwmon"))), None)

        if not hwmon_dir:
            return None

        fname = os.path.join(self.path, "hwmon", hwmon_dir, file_name)
        with open(fname) as fd:
            dat = fd.read().strip()

        return dat

    @property
    def current_power(self):
        """Return current power in milliwatts."""
        m = self.get_metrics()
        try:
            w = m.current_socket_power
        except AttributeError:
            w = m.average_socket_power

        mw = w * 1000000
        return mw

    @property
    def power_limit(self):
        """Return current power limit in milliwatts."""
        return int(self._hwmon_data("power1_cap"))


class MemoryDescriptorMixin:
    @property
    def vram_used(self):
        return int(self.drm_file_info("mem_info_vram_used"))

    @property
    def vram_total(self):
        return int(self.drm_file_info("mem_info_vram_total"))


class DeviceInfo(MemoryDescriptorMixin, PowerDescriptorMixin):
    def __init__(self, path):
        self.path = path

    @property
    def name(self):
        default_name = "UNKNOWN"

        try:
            return self.drm_file_info("product_name")
        except FileNotFoundError:
            pass

        return search_pci_ids(self.device_id[2:]) or default_name

    @property
    def guid(self):
        with open(os.path.join(self.path, "unique_id")) as fd:
            return fd.read().strip()

    @property
    def device_id(self):
        with open(os.path.join(self.path, "device")) as fd:
            dat = fd.read().strip()

        return dat

    def get_metrics(self):
        with open(os.path.join(self.path, "gpu_metrics"), "rb") as fd:
            dat = fd.read()

        mh = MetricsHeader.from_buffer_copy(dat[:4])
        if mh.content_revision == 3:
            return Metrics_1_3.from_buffer_copy(dat)
        elif mh.content_revision == 5:
            return Metrics_1_5.from_buffer_copy(dat)
        else:
            raise NotImplementedError

    def drm_file_info(self, file_name):
        with open(os.path.join(self.path, file_name)) as fd:
            return fd.read().strip()

    def get_clock_info(self):
        return read_clocks(os.path.join(self.path, "pp_dpm_sclk"))


def get_device_info(handle):
    return DeviceInfo(ctop(handle))


def ctop(card):
    return "/sys/class/drm/%s/device" % card


def main():
    devices = iter_devices()

    for d in devices:
        dat = get_device_info(d).get_metrics()
        print_struct(dat)


if __name__ == "__main__":
    main()
