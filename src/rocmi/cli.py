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

import argparse
import logging

from prettytable import PrettyTable, PLAIN_COLUMNS

import rocmi


def parse_args():
    p = argparse.ArgumentParser()
    subps = p.add_subparsers(dest="action", required=True)

    ld = subps.add_parser("list-devices")
    ld.add_argument("--format", choices=["TABLE", "COLUMN"], default="TABLE")

    ps = subps.add_parser("list-processes")

    return p.parse_args()


def main():
    args = parse_args()

    if args.action == "list-devices":

        tab = PrettyTable()
        tab.align = "l"
        if args.format == "COLUMN":
            tab.set_style(PLAIN_COLUMNS)

        tab.field_names = [
            "INDEX",
            "ID",
            "SERIAL",
            "NAME",
            "DRM_PATH",
            "BUS_ID",
            "PROCESSES",
        ]
        for i, card in enumerate(rocmi.get_devices()):
            processes = list(
                map(lambda x: "%s(%d)" % (x.name, x.pid), card.get_processes())
            )
            tab.add_row(
                [
                    i,
                    card.unique_id,
                    card.serial,
                    card.name,
                    card.path,
                    card.bus_id,
                    processes,
                ]
            )

        print(tab)

    elif args.action == "list-processes":
        tab = PrettyTable()
        tab.align = "l"

        tab.field_names = [
            "PID",
            "PASID",
            "NAME",
            "VRAM",
            "SDMA_USAGE",
            "CU_OCCUPANCY",
            "GPUS",
        ]
        ps = rocmi.get_processes()
        for p in ps:
            tab.add_row(
                [
                    p.pid,
                    p.pasid,
                    p.name,
                    p.vram_usage,
                    p.sdma_usage,
                    p.cu_occupancy,
                    p.gpus or None,
                ]
            )

        print(tab)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
