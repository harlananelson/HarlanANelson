import yaml
import os

def add_qmd_to_yaml(qmd_file, yaml_file='_quarto.yml', position='left', index=None):
    """
    Add a new .qmd file to the _quarto.yml navigation.

    Args:
    qmd_file (str): Name of the .qmd file to add.
    yaml_file (str): Path to the _quarto.yml file. Defaults to '_quarto.yml'.
    position (str): Where to add the file in the navbar. Either 'left' or 'right'. Defaults to 'left'.
    index (int): The position to insert the new file. If None, appends to the end. Defaults to None.

    Returns:
    str: A message indicating the result of the operation.
    """
    # Check if the file exists
    if not qmd_file.endswith('.qmd'):
        qmd_file += '.qmd'

    if not os.path.exists(qmd_file):
        raise FileNotFoundError(f"{qmd_file} does not exist.")

    # Read the existing _quarto.yml file
    with open(yaml_file, 'r') as file:
        quarto_config = yaml.safe_load(file)

    # Ensure the navbar and position exist
    if 'website' not in quarto_config:
        quarto_config['website'] = {}
    if 'navbar' not in quarto_config['website']:
        quarto_config['website']['navbar'] = {}
    if position not in quarto_config['website']['navbar']:
        quarto_config['website']['navbar'][position] = []

    navbar = quarto_config['website']['navbar'][position]

    # Check if the file is already in the navbar
    for item in navbar:
        if isinstance(item, str) and item == qmd_file:
            return f"{qmd_file} is already in the navbar."
        elif isinstance(item, dict) and item.get('href') == qmd_file:
            return f"{qmd_file} is already in the navbar."

    # Add the new file to the navbar
    if index is None:
        navbar.append(qmd_file)
    else:
        navbar.insert(index, qmd_file)

    # Write the updated YAML back to the file
    with open(yaml_file, 'w') as file:
        yaml.dump(quarto_config, file, default_flow_style=False)

    return f"Added {qmd_file} to {yaml_file} successfully in the {position} navbar."
def add_qmd_to_yaml(qmd_file, yaml_file='_quarto.yml', position='left', index=None):
    """
    Add a new .qmd file to the _quarto.yml navigation.

    Args:
    qmd_file (str): Name of the .qmd file to add.
    yaml_file (str): Path to the _quarto.yml file. Defaults to '_quarto.yml'.
    position (str): Where to add the file in the navbar. Either 'left' or 'right'. Defaults to 'left'.
    index (int): The position to insert the new file. If None, appends to the end. Defaults to None.

    Returns:
    str: A message indicating the result of the operation.
    """
    # Check if the file exists
    if not qmd_file.endswith('.qmd'):
        qmd_file += '.qmd'

    if not os.path.exists(qmd_file):
        raise FileNotFoundError(f"{qmd_file} does not exist.")

    # Read the existing _quarto.yml file
    with open(yaml_file, 'r') as file:
        quarto_config = yaml.safe_load(file)

    # Ensure the navbar and position exist
    if 'website' not in quarto_config:
        quarto_config['website'] = {}
    if 'navbar' not in quarto_config['website']:
        quarto_config['website']['navbar'] = {}
    if position not in quarto_config['website']['navbar']:
        quarto_config['website']['navbar'][position] = []

    navbar = quarto_config['website']['navbar'][position]

    # Check if the file is already in the navbar
    for item in navbar:
        if isinstance(item, str) and item == qmd_file:
            return f"{qmd_file} is already in the navbar."
        elif isinstance(item, dict) and item.get('href') == qmd_file:
            return f"{qmd_file} is already in the navbar."

    # Add the new file to the navbar
    if index is None:
        navbar.append(qmd_file)
    else:
        navbar.insert(index, qmd_file)

    # Write the updated YAML back to the file
    with open(yaml_file, 'w') as file:
        yaml.dump(quarto_config, file, default_flow_style=False)

    return f"Added {qmd_file} to {yaml_file} successfully in the {position} navbar."
