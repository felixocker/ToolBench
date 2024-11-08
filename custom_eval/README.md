# custom_eval
Run our custom math tasks from [tulip_agent](https://github.com/HRI-EU/tulip_agent) with our tools using ToolLLM. \
Note that ToolLLM's customized API mode does not support using a tool retriever as of November 2024. This may result in higher costs due to a high number of prompt tokens in case of many tools.

## Steps
1. Set up the directories and files: `bash custom_setup.sh`
2. Possibly update the tool descriptions and tasks using `setup_custom_math.py`
3. Run the experiments with the runner in the top-level directory: `bash runner.sh`
4. Check the results using `log_analysis.py`
5. Don't judge how hacky this has been put together
