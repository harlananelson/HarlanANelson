import argparse
from .core import add_qmd_to_yaml

def main():
    parser = argparse.ArgumentParser(description="Add a new .qmd file to _quarto.yml")
    parser.add_argument("qmd_file", help="Name of the .qmd file to add")
    parser.add_argument("--yaml", default="_quarto.yml", help="Path to the _quarto.yml file")
    parser.add_argument("--position", choices=['left', 'right'], default='left', help="Position in navbar (left or right)")
    parser.add_argument("--index", type=int, help="Index position in the navbar (0-based)")
    args = parser.parse_args()

    try:
        result = add_qmd_to_yaml(args.qmd_file, args.yaml, args.position, args.index)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")
if __name__ == "__main__":
    main()
