import os
import pydoc
import sys
import shutil
import re

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
        return True
    except Exception as e:
        # Log any exceptions
        print(f"Error generating documentation for {module_name}: {e}")
        return False

# Generate documentation for all modules
modules = (
    "skytree",
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
    "skytree.tools",
    "skytree.updateable",
    "skytree.user_interface"
)

# Track success/failure
generated_files = []

for module in modules:
    if generate_module_doc(module):
        generated_html = f"{module}.html"
        if os.path.exists(generated_html):
            generated_files.append(generated_html)
        else:
            print(f"Warning: Generated file for {module} not found.")
            # Cleanup and stop further processing
            print("Errors occurred. Cleaning up generated files...")
            for file in generated_files:
                if os.path.exists(file):
                    os.remove(file)
            exit(1)
    else:
        # Cleanup and stop further processing
        print("Errors occurred. Cleaning up generated files...")
        for file in generated_files:
            if os.path.exists(file):
                os.remove(file)
        exit(1)

print("All documentation generated successfully. Clearing docs/ directory...")

# Clear the docs/ directory
for file in os.listdir(docs_dir):
    file_path = os.path.join(docs_dir, file)
    if os.path.isfile(file_path) and file.endswith('.html'):
        os.remove(file_path)

# Move generated files to docs/
for file in generated_files:
    shutil.move(file, os.path.join(docs_dir, file))
print("Documentation moved to docs/.")

# Function to process a single HTML file
def process_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Remove the <td class="extra"> completely
    content = re.sub(r'<td class="extra">.*?</td>', '', content, flags=re.DOTALL)

    # Step 2: Handle broken links
    def replace_links(match):
        href = match.group(1)
        link_text = match.group(2)
        # Check if the file exists within the folder
        if not os.path.exists(os.path.join(docs_dir, href.split("#")[0])) and href != "https://creativecommons.org/licenses/by-nc-sa/4.0/":
            return f'<span style="color: #000099; font-style: italic;">{link_text}</span>'  # Darker blue, italics
        return match.group(0)  # Keep the link as-is if valid

    content = re.sub(r'<a href="([^"]+)">([^<]+)</a>', replace_links, content)

    # Save the modified HTML back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Process all .html files in the docs directory
for file_name in os.listdir(docs_dir):
    if file_name.endswith('.html'):
        file_path = os.path.join(docs_dir, file_name)
        print(f"Processing {file_path}...")
        process_html(file_path)

print("HTML post-processing complete.")
