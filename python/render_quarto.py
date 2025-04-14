import yaml
import subprocess

# Read the _quarto.yml file
with open('_quarto.yml', 'r') as file:
    quarto_config = yaml.safe_load(file)

# Extract the .qmd files from the navbar
files_to_render = []
for item in quarto_config['website']['navbar']['left']:
    if isinstance(item, dict) and 'href' in item:
        files_to_render.append(item['href'])
    elif isinstance(item, str) and item.endswith('.qmd'):
        files_to_render.append(item)

# Run quarto render with the extracted files
cmd = ['quarto', 'render', '--file-name'] + files_to_render
subprocess.run(cmd)
