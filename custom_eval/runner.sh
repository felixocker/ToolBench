#!/bin/bash

# Simple runner for ToolBench w DSFDT
# Usage: bash runner.sh

export PYTHONPATH=./
source .venv/bin/activate
python toolbench/inference/qa_pipeline.py \
    --tool_root_dir data/toolenv/tools/ \
    --backbone_model chatgpt_function \
    --openai_key $OPENAI_API_KEY \
    --max_observation_length 1024 \
    --method DFS_woFilter_w2 \
    --input_query_file data/instruction/custom_query.json \
    --output_answer_file data/answer/custom_result \
    --api_customization

