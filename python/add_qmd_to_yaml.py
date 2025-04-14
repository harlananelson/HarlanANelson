import yaml
import sys
import os

def add_qmd_to_yaml(qmd_file):
    # Check if the file exists
    if not qmd_file.endswith('.qmd'):
        qmd_file += '.qmd'
    
    if not os.path.exists(qmd_file):
        print(f"Error: {qmd_file} does not exist.")
        return

    # Read the existing _quarto.yml file
    with open('_quarto.yml', 'r') as file:
        quarto_config = yaml.safe_load(file)

    # Add the new qmd file to the navbar
    if 'website' in quarto_config and 'navbar' in quarto_config['website']:
        if 'left' not in quarto_config['website']['navbar']:
            quarto_config['website']['navbar']['left'] = []
        
        # Check if the file is already in the navbar
        for item in quarto_config['website']['navbar']['left']:
            if isinstance(item, str) and item == qmd_file:
                print(f"{qmd_file} is already in the navbar.")
                return
            elif isinstance(item, dict) and item.get('href') == qmd_file:
                print(f"{qmd_file} is already in the navbar.")
                return

        # Add the new file to the navbar
        quarto_config['website']['navbar']['left'].append(qmd_file)
    else:
        print("Error: 'website' or 'navbar' section not found in _quarto.yml")
        return

    # Write the updated YAML back to the file
    with open('_quarto.yml', 'w') as file:
        yaml.dump(quarto_config, file, default_flow_style=False)

    print(f"Added {qmd_file} to _quarto.yml successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_qmd_to_yaml.py <qmd_file>")
    else:
        add_qmd_to_yaml(sys.argv[1])
