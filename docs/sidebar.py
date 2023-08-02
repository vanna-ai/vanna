import yaml

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

# Read YAML data from a file
def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        yaml_data = file.read()
    return yaml_data

file_path = 'sidebar.yaml'  # Replace this with the actual path to your YAML file

yaml_data = read_yaml_file(file_path)

# Parse YAML data
sidebar_data = yaml.safe_load(yaml_data)

# Generate HTML code
html_code = generate_html(sidebar_data, 'vn-ask.html')
print(html_code)

import nbformat

# Read notebook file
current_notebook = nbformat.read('vn-ask.ipynb', as_version=4)

from nbconvert import HTMLExporter
html_exporter = HTMLExporter(template_name='blog')

(body, resources) = html_exporter.from_notebook_node(current_notebook)

# Write body to file
with open('vn-ask.html', 'w') as file:
    file.write(body.replace('<!-- NAV HERE -->', html_code))
