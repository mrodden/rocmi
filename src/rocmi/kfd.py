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


import logging
import os
from collections import namedtuple


LOG = logging.getLogger(__name__)


ComputeProcess = namedtuple(
    "ComputeProcess",
    [
        "pid", # unix process ID
        "pasid", # Process Address Space ID
        "name",
        "vram_usage", # bytes
        "sdma_usage", # microseconds
        "cu_occupancy", # percent
    ],
)


def get_processes():
    parent = "/sys/class/kfd/kfd/proc"
    procs = []
    for proc_dir in os.listdir(parent):

        try:
            pid = int(proc_dir)
        except ValueError:
            continue

        with open(os.path.join(parent, proc_dir, "pasid")) as fd:
            pasid = int(fd.read().strip())

        vram_usage, sdma_usage, cu_occupancy = _read_kfd_usages(pid)

        procs.append(ComputeProcess(pid=pid, pasid=pasid, name=read_process_name(pid), vram_usage=vram_usage, sdma_usage=sdma_usage, cu_occupancy=cu_occupancy))

    return procs


def read_process_name(pid):
    with open("/proc/%d/comm" % pid, "r") as fd:
        return fd.read().strip()


def _read_kfd_usages(pid):
    parent = "/sys/class/kfd/kfd/proc/%d" % pid
    vram_usage = 0
    sdma_usage = 0
    cu_occupancy = 0

    def read_int(path):
        with open(path, "r") as fd:
            return int(fd.read().strip())

    for fname in os.listdir(parent):
        if fname.startswith("vram_"):
            vram_usage += read_int(os.path.join(parent, fname))

        elif fname.startswith("sdma_"):
            sdma_usage += read_int(os.path.join(parent, fname))

        elif fname.startswith("stats_"):
            cu_occupancy += read_int(os.path.join(parent, fname, "cu_occupancy"))

    return vram_usage, sdma_usage, cu_occupancy


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


def read_process_fdinfos(pid):
    parent = "/proc/%d/fdinfo" % pid

    vram_kib = 0

    for fdinfo in os.listdir(parent):
        kvs = {}

        with open(os.path.join(parent, fdinfo), "r") as fd:
            for line in fd.readlines():
                key, rest = line.strip().split(":", 1)
                if key == "drm-memory-vram":
                    kib, _ = rest.strip().split(" ")
                    vram_kib += int(kib)

                kvs[key] = rest.strip()

        LOG.info(f"{kvs=}")

    return vram_kib



