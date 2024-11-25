import os
import pydoc
import sys
import shutil

# Set the package name (the top-level package you're documenting)
package_name = "skytree"

# Set the path to the 'src' folder (where your package is located)
package_path = os.path.join(os.getcwd(), 'src')

# Set the output folder for documentation
docs_dir = os.path.join(os.getcwd(), 'docs')

# Make sure the package path is correct
print(f"Package path: {package_path}")
if not os.path.exists(package_path):
    print(f"Error: The directory {package_path} does not exist.")
    exit(1)

# Create the docs directory if it doesn't exist
if not os.path.exists(docs_dir):
    os.makedirs(docs_dir)

# Append the 'src' folder to sys.path so pydoc can locate the package
sys.path.append(package_path)

# Print the current Python path to check if it includes the src folder
print(f"Current PYTHONPATH: {sys.path}")

# Change the current working directory to the 'src' folder
os.chdir(package_path)

# Function to generate documentation for a single module
def generate_module_doc(module_name):
    try:
        # Try to generate the documentation
        print(f"Generating documentation for: {module_name}")
        pydoc.writedoc(module_name)

        # Move the generated .html file to the docs folder
        generated_html = f"{module_name}.html"
        if os.path.exists(generated_html):
            shutil.move(generated_html, os.path.join(docs_dir, generated_html))
            print(f"Moved {generated_html} to {docs_dir}")
        else:
            print(f"Error: Documentation for {module_name} not found.")
    except ImportError as e:
        # Ignore the ImportError and generate whatever doc we can
        print(f"Warning: Could not import {module_name} fully due to import error: {e}")
        # Generate docs anyway (even though imports might not be resolved)
        pydoc.writedoc(module_name)

    except Exception as e:
        # Catch all other exceptions, but allow the script to continue
        print(f"Error generating documentation for {module_name}: {e}")

for module in ("skytree",
               "skytree.game",
               "skytree.animated",
               "skytree.boards",
               "skytree.collidable",
               "skytree.component",
               "skytree.config",
               "skytree.drawable",
               "skytree.examples",
               "skytree.helpers",
               "skytree.key_commands",
               "skytree.layers",
               "skytree.positional",
               "skytree.resource_manager",
               "skytree.singleton",
               "skytree.sprites",
               "skytree.stage",
               "skytree.tile_objects",
               "skytree.tileset",
               "skytree.timers",
               "skytree.updateable",
               "skytree.user_interface"
               ):
    generate_module_doc(module)

print("All documentation has been generated and moved to the docs/ folder.")
