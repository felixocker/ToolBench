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
Analyze logs.
Parts taken from tulip_agent: https://github.com/HRI-EU/tulip_agent
"""
import json
from dataclasses import dataclass, field


MODEL = "gpt-3.5-turbo-0125"


OAI_PRICES = {
    "gpt-3.5-turbo-0125": {
        "input": 0.5 / 1_000_000,
        "output": 1.5 / 1_000_000,
    },
    "gpt-4-turbo-2024-04-09": {
        "input": 10 / 1_000_000,
        "output": 30 / 1_000_000,
    },
    "gpt-4o-2024-05-13": {
        "input": 5 / 1_000_000,
        "output": 15 / 1_000_000,
    },
    "gpt-4o-mini-2024-07-18": {
        "input": 0.15 / 1_000_000,
        "output": 0.60 / 1_000_000,
    },
    "text-embedding-ada-002": 0.1 / 1_000_000,
    "text-embedding-3-small": 0.02 / 1_000_000,
    "text-embedding-3-large": 0.13 / 1_000_000,
}


@dataclass
class Result:
    name: str
    response: str
    prompt_tokens: int
    completion_tokens: int
    costs: float = field(init=False)
    correctness: bool = field(init=False)
    level: str = field(init=False)

    def __post_init__(self) -> None:
        self.costs = round(
            (
                OAI_PRICES[MODEL]["input"] * self.prompt_tokens
                + OAI_PRICES[MODEL]["output"] * self.completion_tokens
            ),
            5,
        )
        self.correctness = False
        self.level = ""


def interquartile_mean(values: list) -> float:
    lnv = len(values)
    q = lnv // 4
    if q == 0:
        return 0.0
    if lnv % 4 == 0:
        nums = values[q:-q]
        return sum(nums) / (2 * q)
    else:
        q_ = lnv / 4
        w = q + 1 - q_
        nums = [values[q] * w] + values[q + 1 : -(q + 1)] + [values[-(q + 1)] * w]
        return sum(nums) / (2 * q_)


def analyze(
    log_file: str = "/hri/localdisk/focker/tmp/ToolBench/data/LOG.txt"
):
    with open(log_file, "r") as f:
        data = f.readlines()

    results = []
    current = {}
    for c, line in enumerate(data):
        if ")]now playing " in line:
            if current:
                results.append(Result(**current))
            current = {
                "name": line.split(")]now playing ")[-1].split(", with ")[0],
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "response": "",
            }
        elif "prompt tokens" in line:
            parts = line.strip().split(",")
            current["prompt_tokens"] += int(parts[0].split(": ")[-1])
            current["completion_tokens"] += int(parts[1].split(": ")[-1])
        elif line.startswith("Action Input: "):
            action_data = json.loads(line.strip().split("Action Input: ")[1])
            if "return_type" in action_data:
                current["response"] = action_data["final_answer"] if "final_answer" in action_data else ""
        if c == len(data)-1:
            results.append(Result(**current))
    return results


def validate(
    results: list[Result],
    tasks_file: str = "../../../../instruction/custom_query.json",
    original_tasks: str = "../../../../math_tasks.json",
):
    print("\nVALIDATING")
    with open(original_tasks, "r") as f:
        original_tasks = json.load(f)
    print(f"{len(original_tasks)} original tasks")
    with open(tasks_file, "r") as f:
        tasks = json.load(f)
    assert len(tasks) == len(original_tasks), f"Only {len(tasks)} tasks"
    for original_task in original_tasks:
        if not any([r for r in results if r.name == original_task["task"]]):
            print(f"No result for task: {original_task['task']}")
    assert len(results) == len(tasks), f"Only {len(results)}/{len(tasks)} results"


def assess(
    results: list[Result],
    tasks_file: str = "../../../../math_tasks.json",
) -> list[Result]:
    with open(tasks_file, "r") as f:
        tasks = json.load(f)
    print(f"{len(tasks)=}")
    task_lookup = {
        task["task"]: task
        for task in tasks
    }
    for result in results:
        task_data = task_lookup[result.name]
        if any([str(valid_solution) in result.response for valid_solution in task_data["valid_solutions"]]):
            result.correctness = True
        result.level = task_data["name"][4]
        if not result.response:
            print(f"No result for {result.name}: {result}")
    return results


def run_statistics(results: list[Result]):
    for abbrev, level in (("E", "Easy"), ("M", "Medium"), ("H", "Hard")):
        print()
        res = [r for r in results if r.level == abbrev]
        print(f"{level}: {len(res)}")
        correct = [r for r in res if r.correctness is True]
        print(f"Correctness: {len(correct)}/{len(res)} = {len(correct)/len(res)}")
        iqm = round(interquartile_mean([r.costs for r in res]), 3)
        print(f"Interquartile mean for costs: {iqm}")


if __name__ == "__main__":
    toolllm_results = analyze()
    validate(toolllm_results)
    assessed_results = assess(toolllm_results)
    run_statistics(assessed_results)
