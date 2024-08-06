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

        tab.field_names = ["INDEX", "ID", "SERIAL", "NAME", "DRM_PATH", "BUS_ID"]
        for i, card in enumerate(rocmi.get_devices()):
            tab.add_row([i, card.unique_id, card.serial, card.name, card.path, card.bus_id])

        print(tab)

    elif args.action == "list-processes":
        for ps in rocmi.get_processes():
            print("%r" % ps)



if __name__ == "__main__":
    main()
