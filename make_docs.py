import os
import pydoc
import sys
import shutil
import re

# Paths
package_name = "skytree"
package_path = os.path.join(os.getcwd(), 'src')
docs_dir = os.path.join(os.getcwd(), 'docs')
if not os.path.exists(package_path):
    print(f"Error: {package_path} --wrong package path.")
    exit(1)
if not os.path.exists(docs_dir):
    os.makedirs(docs_dir)
sys.path.append(package_path)

os.chdir(package_path)

def generate_module_doc(module_name):
    """Generate docs for a single module."""
    try:
        print(f"Generating documentation for: {module_name}")
        pydoc.writedoc(module_name)
        return True
    except Exception as e:
        print(f"Error generating documentation for {module_name}: {e}")
        return False

def process_html(file_path):
    """
    Process a single html file.
    
    Remove unwanted hyperlinks and tweak format.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove links at the top of the page pointing to files
    content = re.sub(r'<td class="extra">.*?</td>', '', content, flags=re.DOTALL)

    # Remove broken links
    def replace_links(match):
        """Check if file exists in the folder, replace by span with specific format otherwise."""
        href = match.group(1)
        link_text = match.group(2)
        # Make an exception for the license link
        if not os.path.exists(os.path.join(docs_dir, href.split("#")[0])) and href != "https://creativecommons.org/licenses/by-nc-sa/4.0/":
            return f'<span style="color: #000099; font-style: italic;">{link_text}</span>'
        return match.group(0)

    content = re.sub(r'<a href="([^"]+)">([^<]+)</a>', replace_links, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Control module order to avoid import issues. Game must be first.
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
generated_files = []

# Generate docs
for module in modules:
    if generate_module_doc(module):
        generated_html = f"{module}.html"
        if os.path.exists(generated_html):
            generated_files.append(generated_html)
        else:
            print(f"Generated file for {module} not found.")
            for file in generated_files:
                if os.path.exists(file):
                    os.remove(file)
            exit(1)
    else:
        print(f"Error while processing {module}. Cleaning up generated files...")
        for file in generated_files:
            if os.path.exists(file):
                os.remove(file)
        exit(1)

# Clear docs/ directory and move all generated files there
print("Clearing docs/ directory...")
for file in os.listdir(docs_dir):
    file_path = os.path.join(docs_dir, file)
    if os.path.isfile(file_path) and file.endswith('.html'):
        os.remove(file_path)
for file in generated_files:
    shutil.move(file, os.path.join(docs_dir, file))
print("Documentation moved to docs/.")

# Process all .html files in the docs directory
for file_name in os.listdir(docs_dir):
    if file_name.endswith('.html'):
        file_path = os.path.join(docs_dir, file_name)
        print(f"Processing {file_path}...")
        process_html(file_path)
print("Documentation generated successfully!")
