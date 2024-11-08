BASE_DIR="../data"

mkdir -p "$BASE_DIR/answer/"
mkdir -p "$BASE_DIR/instruction/"
mkdir -p "$BASE_DIR/toolenv/tools/Customized/custom_math/"

cp "custom_stuff/custom_query.json" "../data/instruction/custom_query.json"
cp "custom_stuff/LOG.txt" "../data/LOG.txt"
cp "custom_stuff/math_tasks.json" "../data/math_tasks.json"
cp "custom_stuff/api.py" "../data/toolenv/tools/Customized/custom_math/api.py"
cp "custom_stuff/log_analysis.py" "../data/toolenv/tools/Customized/custom_math/log_analysis.py"
cp "custom_stuff/requirements.txt" "../data/toolenv/tools/Customized/custom_math/requirements.txt"
cp "custom_stuff/setup_custom_math.py" "../data/toolenv/tools/Customized/custom_math/setup_custom_math.py"
cp "custom_stuff/custom_math.json" "../data/toolenv/tools/Customized/custom_math.json"
cp "runner.sh" "../runner.sh"

echo "For regenerating the tool descriptions from api.py run setup_custom_math.py. Requires deps."
echo "Done. Now run runner.sh in the top-level directory."
echo "For analyzing results run log_analysis.py"
