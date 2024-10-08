#!/usr/bin/env python
# -*- coding: utf-8 -*-
###
# Copyright (2016-2024) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: ilo_redfish_info
short_description: Gathers server information through iLO using Redfish APIs
version_added: 4.2.0
description:
  - Builds Redfish URIs locally and sends them to iLO to
    get information back.
  - For use with HPE iLO operations that require Redfish OEM extensions.
options:
  category:
    required: true
    description:
      - List of categories to execute on iLO.
    type: list
    elements: str
  command:
    required: true
    description:
      - List of commands to execute on iLO.
    type: list
    elements: str
  baseuri:
    required: true
    description:
      - Base URI of iLO.
    type: str
  username:
    description:
      - User for authentication with iLO.
    type: str
  password:
    description:
      - Password for authentication with iLO.
    type: str
  auth_token:
    description:
      - Security token for authentication with iLO.
    type: str
    version_added: 2.3.0
  timeout:
    description:
      - Timeout in seconds for URL requests to iLO.
    default: 10
    type: int
author:
    - "Bhavya B (@bhavya06)"
"""

EXAMPLES = """
  - name: Get iLO Sessions
    community.general.ilo_redfish_info:
      category: Sessions
      command: GetiLOSessions
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result_sessions
"""

RETURN = """
ilo_redfish_info:
    description: Returns iLO sessions.
    type: dict
    contains:
        GetiLOSessions:
            description: Returns the iLO session msg and whether the function executed successfully.
            type: dict
            contains:
                ret:
                    description: Check variable to see if the information was succesfully retrived.
                    type: bool
                msg:
                    description: Information of all active iLO sessions.
                    type: list
                    elements: dict
                    contains:
                        Description:
                            description: Provides a description of the resource.
                            type: str
                        Id:
                            description: The sessionId.
                            type: str
                        Name:
                            description: The name of the resource.
                            type: str
                        UserName:
                            description: Name to use to log in to the management processor.
                            type: str
    returned: always
"""

CATEGORY_COMMANDS_ALL = {"Sessions": ["GetiLOSessions"]}

CATEGORY_COMMANDS_DEFAULT = {"Sessions": "GetiLOSessions"}

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.general.plugins.module_utils.ilo_redfish_utils import (
    iLORedfishUtils,
)


def main():
    result = {}
    category_list = []
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(required=True, type="list", elements="str"),
            command=dict(required=True, type="list", elements="str"),
            baseuri=dict(required=True),
            username=dict(),
            password=dict(no_log=True),
            auth_token=dict(no_log=True),
            timeout=dict(type="int", default=10),
        ),
        required_together=[
            ("username", "password"),
        ],
        required_one_of=[
            ("username", "auth_token"),
        ],
        mutually_exclusive=[
            ("username", "auth_token"),
        ],
        supports_check_mode=True,
    )

    creds = {
        "user": module.params["username"],
        "pswd": module.params["password"],
        "token": module.params["auth_token"],
    }

    timeout = module.params["timeout"]

    root_uri = "https://" + module.params["baseuri"]
    rf_utils = iLORedfishUtils(creds, root_uri, timeout, module)

    # Build Category list
    if "all" in module.params["category"]:
        for entry in CATEGORY_COMMANDS_ALL:
            category_list.append(entry)
    else:
        # one or more categories specified
        category_list = module.params["category"]

    for category in category_list:
        command_list = []
        # Build Command list for each Category
        if category in CATEGORY_COMMANDS_ALL:
            if not module.params["command"]:
                # True if we don't specify a command --> use default
                command_list.append(CATEGORY_COMMANDS_DEFAULT[category])
            elif "all" in module.params["command"]:
                for entry in CATEGORY_COMMANDS_ALL[category]:
                    command_list.append(entry)
            # one or more commands
            else:
                command_list = module.params["command"]
                # Verify that all commands are valid
                for cmd in command_list:
                    # Fail if even one command given is invalid
                    if cmd not in CATEGORY_COMMANDS_ALL[category]:
                        module.fail_json(msg="Invalid Command: %s" % cmd)
        else:
            # Fail if even one category given is invalid
            module.fail_json(msg="Invalid Category: %s" % category)

        # Organize by Categories / Commands
        if category == "Sessions":
            for command in command_list:
                if command == "GetiLOSessions":
                    result[command] = rf_utils.get_ilo_sessions()

    module.exit_json(ilo_redfish_info=result)


if __name__ == "__main__":
    main()
