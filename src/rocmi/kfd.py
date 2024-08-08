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

import binascii
import logging
import os
from collections import namedtuple


LOG = logging.getLogger(__name__)


ComputeProcess = namedtuple(
    "ComputeProcess",
    [
        "pid",  # unix process ID
        "pasid",  # Process Address Space ID
        "name",  # command name for process
        "vram_usage",  # bytes
        "sdma_usage",  # microseconds
        "cu_occupancy",  # percent
        "gpus",  # set of KFD gpu_ids
        "gpu_usage_info",
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

        vram_usage, sdma_usage, cu_occupancy, gpu_infos = _read_kfd_usages(pid)
        gpus = _gpu_ids_for_pid(pid)

        p = ComputeProcess(
            pid=pid,
            pasid=pasid,
            name=read_process_name(pid),
            vram_usage=vram_usage,
            sdma_usage=sdma_usage,
            cu_occupancy=cu_occupancy,
            gpus=gpus,
            gpu_usage_info=gpu_infos,
        )
        procs.append(p)

    return procs


def read_process_name(pid):
    """Return command name associated with PID."""

    with open("/proc/%d/comm" % pid, "r") as fd:
        return fd.read().strip()


def _gpu_ids_for_pid(pid):
    return set(map(lambda x: x["gpuid"], _read_queues_for_pid(pid)))


def _read_queues_for_pid(pid):
    parent = "/sys/class/kfd/kfd/proc/%d/queues" % pid
    queues = []

    for queue_dir in os.listdir(parent):
        queue = {"id": queue_dir}
        for f in os.listdir(os.path.join(parent, queue_dir)):
            fp = os.path.join(parent, queue_dir, f)
            queue[f] = _read_int(fp)

        queues.append(queue)

    return queues


def _read_kfd_usages(pid):
    parent = "/sys/class/kfd/kfd/proc/%d" % pid

    # totals
    vram_usage = 0
    sdma_usage = 0
    cu_occupancy = 0
    cu_occupancy_count = 0

    # individual gpus
    gpus = {}

    for fname in os.listdir(parent):
        try:
            typ, gpu_id = fname.split("_")
            gpu_id = int(gpu_id)
        except ValueError:
            continue

        if typ == "stats":
            val = _read_int(os.path.join(parent, fname, "cu_occupancy"))
            cu_occupancy_count += 1
        elif typ in ["vram", "sdma"]:
            val = _read_int(os.path.join(parent, fname))
        else:
            continue

        if gpus.get(gpu_id) is None:
            gpus[gpu_id] = {}

        gpus[gpu_id][typ] = val

        if typ == "vram":
            vram_usage += val
        elif typ == "sdma":
            sdma_usage += val
        elif typ == "stats":
            cu_occupancy += val

    return vram_usage, sdma_usage, cu_occupancy, gpus


def _read_int(path):
    with open(path, "r") as fd:
        return int(fd.read().strip())


def _read_str(path):
    with open(path, "r") as fd:
        return fd.read().strip()


def _read_props(path):
    kvs = {}

    with open(path, "r") as fd:
        for line in fd.readlines():
            k, v = line.strip().split(" ")

            try:
                v = int(v)
            except ValueError:
                pass

            kvs[k] = v

    return kvs


class KFDNode:

    def __init__(self, path, gpu_id, props):
        self.path = path
        self.props = props
        self.gpu_id = gpu_id

    @property
    def unique_id_as_int(self):
        return self.props.get("unique_id")

    @property
    def unique_id(self):
        uid = self.unique_id_as_int

        if not uid is None:
            return binascii.hexlify(uid.to_bytes(8, "big")).decode("utf8")

        return None


def _iter_kfd_devices():
    parent = "/sys/class/kfd/kfd/topology/nodes"

    gpus = []

    for node in os.listdir(parent):
        for fp in os.listdir(os.path.join(parent, node)):
            if fp == "gpu_id":
                gpu_id = _read_int(os.path.join(parent, node, "gpu_id"))
                props = _read_props(os.path.join(parent, node, "properties"))
                if props.get("unique_id"):
                    gpus.append(KFDNode(os.path.join(parent, node), gpu_id, props))

    return gpus


unique_to_kfd = {s.unique_id: s for s in _iter_kfd_devices()}


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

    return vram_kib
