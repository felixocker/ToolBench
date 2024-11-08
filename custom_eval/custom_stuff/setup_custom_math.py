#!/usr/bin/env python3
#
# Copyright (c) 2024, Honda Research Institute Europe GmbH
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
Analysis of Python functions and entire classes using introspection
for creating descriptions usable with the OpenAI API

Taken from tulip_agent: https://github.com/HRI-EU/tulip_agent

Note: Function calling w structured outputs is limited to a subset of the JSON schema language
https://platform.openai.com/docs/guides/function-calling
"""
import importlib
import json

from inspect import getmembers, isfunction

import pydantic


class FunctionAnalyzer:

    @staticmethod
    def analyze_function(function_) -> dict:
        """
        Analyzes a python function and returns a description compatible with the OpenAI API
        Assumptions:
        * docstring includes a function description and parameter descriptions separated by 2 linebreaks
        * docstring includes parameter descriptions indicated by :param x:
        """
        name = function_.__name__

        # analyze type hints
        parameters = pydantic.TypeAdapter(function_).json_schema()

        # analyze doc string
        descriptions = [e.strip() for e in function_.__doc__.split(":param ")]
        function_description, parameter_descriptions = descriptions[0], descriptions[1:]
        parameter_descriptions = {
            k: v
            for (k, v) in [
                e.split(":return:")[0].strip().split(": ")
                for e in parameter_descriptions
                if e
            ]
        }
        for parameter, parameter_description in parameter_descriptions.items():
            parameters["properties"][parameter]["description"] = parameter_description

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": function_description,
                "parameters": parameters,
            },
            "strict": True,
        }


def prepare_tools(
    module_name: str = "api",
    custom_math_definition: str = "../custom_math.json",
    array_support: bool = True,
):
    module = importlib.import_module(module_name)
    print(module)
    functions = [
        (n, f)
        for n, f in getmembers(module, isfunction)
        if f.__module__ == module_name
    ]
    print(f"Number of functions: {len(functions)}")
    print(f"Functions: {functions}")
    print(f"Number of duplicate functions: {len(functions) - len(set(functions))}")

    api_list = []
    api_name_list = []
    fa = FunctionAnalyzer()
    for name, function in functions:
        # print(name)
        data = fa.analyze_function(function)
        # print(data)

        params = []
        for k, v in data["function"]["parameters"]["properties"].items():
            param = {
                "name": k,
                "type": v["type"],
                "description": v["description"],
                "default": None
            }
            if array_support:
                if "items" in v:
                    param["items"] = v["items"]
            params.append(param)

        if array_support is False:
            supported_types = ("number", "integer", "string", "boolean")
        else:
            supported_types = ("number", "integer", "string", "boolean", "array")
        if any([p["type"] not in supported_types for p in params]):
            continue

        api_data = {
            "name": name,
            "url": "",
            "description": data["function"]["description"],
            "method": "GET",
            "required_parameters": params,
            "optional_parameters": []
        }
        api_list.append(api_data)
        api_name_list.append(
            {
                "category_name": "Customized",
                "tool_name": "custom math",
                "api_name": name
            }
        )

    api_description = {
        "tool_description": "Custom math functions.",
        "tool_name": "custom math",
        "title": "custom math",
        "api_list": api_list,
        "standardized_name": "custom_math"
    }

    # write to api definition
    with open(custom_math_definition, "w") as f:
        json.dump(api_description, f, indent=4)

    return api_name_list


def prepare_queries(
    api_list_definition: list,
    task_file: str = "../../../../math_tasks.json",
    instruction_file: str = "../../../../instruction/custom_query.json",
):
    with open(task_file, "r") as f:
        tasks = json.load(f)

    name_lookup = {
        "E": "1",
        "M": "2",
        "H": "3",
    }
    query_list = []
    for task in tasks:
        query_name_parts = task["name"].split(".")
        query = {
            "query": task["task"],
            "query_id": int(name_lookup[query_name_parts[-2]] + query_name_parts[-1]),
            "api_list": api_list_definition
        }
        query_list.append(query)

    with open(instruction_file, "w") as f:
        json.dump(query_list, f, indent=4)


if __name__ == "__main__":
    api_list_file = "../../api_list.json"
    api_name_list = prepare_tools()
    prepare_queries(api_list_definition=api_name_list)
