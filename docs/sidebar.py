import yaml
import sys
import nbformat
from nbconvert import HTMLExporter

# Get the yaml file path from the command line
file_path = sys.argv[1]

# Get the directory to search for the .ipynb files from the command line
notebook_dir = sys.argv[2]

# Get the output directory from the command line
output_dir = sys.argv[3]

def generate_html(sidebar_data, current_path: str):
    html = '<ul class="space-y-2">\n'
    for entry in sidebar_data:
        html += '<li>\n'
        if 'sub_entries' in entry:
            # Dropdown menu with sub-entries
            html += f'<button type="button" class="flex items-center p-2 w-full text-base font-normal text-gray-900 rounded-lg transition duration-75 group hover:bg-gray-100 dark:text-white dark:hover:bg-gray-700" aria-controls="dropdown-{entry["title"]}" data-collapse-toggle="dropdown-{entry["title"]}">\n'
            html += f'{entry["svg_text"]}\n'
            html += f'<span class="flex-1 ml-3 text-left whitespace-nowrap">{entry["title"]}</span>\n'
            html += '<svg aria-hidden="true" class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>\n'
            html += '</button>\n'
            html += f'<ul id="dropdown-{entry["title"]}" class="hidden py-2 space-y-2">\n'
            for sub_entry in entry['sub_entries']:
                html += f'<li>\n'
                highlighted = 'bg-indigo-100 dark:bg-indigo-700' if sub_entry['link'] == current_path else ''
                html += f'<a href="{sub_entry["link"]}" class="flex items-center p-2 pl-11 w-full text-base font-normal text-gray-900 rounded-lg transition duration-75 group hover:bg-gray-100 dark:text-white dark:hover:bg-gray-700 {highlighted}">{sub_entry["title"]}</a>\n'
                html += '</li>\n'
            html += '</ul>\n'
        else:
            # Regular sidebar entry without sub-entries
            highlighted = 'bg-indigo-100 dark:bg-indigo-700' if entry['link'] == current_path else ''
            html += f'<a href="{entry["link"]}" class="flex items-center p-2 text-base font-normal text-gray-900 rounded-lg dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 group {highlighted}">\n'
            html += f'{entry["svg_text"]}\n'
            html += f'<span class="ml-3">{entry["title"]}</span>\n'
            html += '</a>\n'
        html += '</li>\n'
    html += '</ul>'
    return html

def generate_header(notebook_name: str) -> str:
    return f"""
<a href="https://colab.research.google.com/github/vanna-ai/vanna-py/blob/main/notebooks/{notebook_name}.ipynb" target="_blank" class="text-white bg-indigo-700 hover:bg-indigo-800 focus:ring-4 focus:outline-none focus:ring-indigo-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center mr-2 dark:bg-indigo-600 dark:hover:bg-indigo-700 dark:focus:ring-indigo-800">
  <svg class="w-3.5 h-3.5 mr-2" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 14 16">
    <path d="M0 .984v14.032a1 1 0 0 0 1.506.845l12.006-7.016a.974.974 0 0 0 0-1.69L1.506.139A1 1 0 0 0 0 .984Z"/>
  </svg>
  Run Using Colab
</a>
<a href="https://github.com/vanna-ai/vanna-py/blob/main/notebooks/{notebook_name}.ipynb" target="_blank" class="text-white bg-[#24292F] hover:bg-[#24292F]/90 focus:ring-4 focus:outline-none focus:ring-[#24292F]/50 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center dark:focus:ring-gray-500 dark:hover:bg-[#050708]/30 mr-2 mb-2">
  <svg class="w-4 h-4 mr-2" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
    <path fill-rule="evenodd" d="M10 .333A9.911 9.911 0 0 0 6.866 19.65c.5.092.678-.215.678-.477 0-.237-.01-1.017-.014-1.845-2.757.6-3.338-1.169-3.338-1.169a2.627 2.627 0 0 0-1.1-1.451c-.9-.615.07-.6.07-.6a2.084 2.084 0 0 1 1.518 1.021 2.11 2.11 0 0 0 2.884.823c.044-.503.268-.973.63-1.325-2.2-.25-4.516-1.1-4.516-4.9A3.832 3.832 0 0 1 4.7 7.068a3.56 3.56 0 0 1 .095-2.623s.832-.266 2.726 1.016a9.409 9.409 0 0 1 4.962 0c1.89-1.282 2.717-1.016 2.717-1.016.366.83.402 1.768.1 2.623a3.827 3.827 0 0 1 1.02 2.659c0 3.807-2.319 4.644-4.525 4.889a2.366 2.366 0 0 1 .673 1.834c0 1.326-.012 2.394-.012 2.72 0 .263.18.572.681.475A9.911 9.911 0 0 0 10 .333Z" clip-rule="evenodd"/>
  </svg>
  Open in GitHub
</a>
"""    

# Read YAML data from a file
def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        yaml_data = file.read()
    return yaml_data

yaml_data = read_yaml_file(file_path)

# Parse YAML data
sidebar_data = yaml.safe_load(yaml_data)

# Get a list of all .ipynb files in the directory
import os
notebook_files = [file for file in os.listdir(notebook_dir) if file.endswith('.ipynb')]

def is_runnable(notebook_name: str, sidebar_data: dict) -> bool:
    # Check if the notebook is runnable
    for entry in sidebar_data:
        if 'link' in entry:
            if entry['link'] == f'{notebook_name}.html':
                return entry.get('runnable', 'true') == 'true'
            
        if 'sub_entries' in entry:
            for sub_entry in entry['sub_entries']:
                if sub_entry['link'] == f'{notebook_name}.html':
                    return sub_entry.get('runnable', 'true') == 'true'

    return False

for notebook_file in notebook_files:
    # Get just the file name without the extension
    notebook_name = os.path.splitext(notebook_file)[0]

    # Get the full path to the notebook
    notebook_file_path = os.path.join(notebook_dir, notebook_file)

    # Generate HTML code
    html_code = generate_html(sidebar_data, f'{notebook_name}.html')

    # Read notebook file
    current_notebook = nbformat.read(notebook_file_path, as_version=4)

    html_exporter = HTMLExporter(template_name='nb-theme')

    (body, resources) = html_exporter.from_notebook_node(current_notebook)

    # Write body to file
    with open(os.path.join(output_dir, f'{notebook_name}.html'), 'w') as file:
        # From sidebar_data, see if there is a matching entry for the current notebook
        if is_runnable(notebook_name, sidebar_data):
            file.write(body.replace('<!-- NAV HERE -->', html_code).replace('<!-- HEADER HERE -->', generate_header(notebook_name)))
        else:
            file.write(body.replace('<!-- NAV HERE -->', html_code))


