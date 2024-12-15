import glob
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re

def month_year_from_filename(filename):
    # Extract the date part from the filename
    date_time_part = filename.split(']')[0].strip('[')
    date_part = date_time_part.split(' ')[0]
    month, day, year = date_part.split('-')
    month_name = datetime.strptime(month, '%m').strftime('%B')
    full_year = '20' + year
    return f"{month_name}{full_year}", datetime.strptime(f"{day}-{month}-{full_year}", '%d-%m-%Y')

def sanitize_filename(filename):
    # Remove time and unnecessary parts from the filename
    sanitized_name = filename.replace(' - Chat.html', '').replace('[', '').replace(']', '')
    date_part, time_part_rest = sanitized_name.split(' ', 1)
    time_part, rest = time_part_rest.split(' ', 1)
    month, day, year = date_part.split('-')
    sanitized_name = f"{day}-{month}-{year} {rest}"
    return sanitized_name

def modify_html_files(html_dir: str):
    chat_files = glob.glob(os.path.join(html_dir, '*.html'))
    chat_files_details = []

    for path in chat_files:
        filename = os.path.basename(path)
        month_year, sort_date = month_year_from_filename(filename)
        sanitized_filename = sanitize_filename(filename)
        final_path = os.path.join(html_dir, f"{sanitized_filename}.html")
        chat_files_details.append((path, sanitized_filename, month_year, sort_date, final_path))

    chat_files_details.sort(key=lambda x: x[3])

    js_snippet = """
<script type="module" src="https://cdn.jsdelivr.net/npm/@bufferhead/nightowl@0.0.14/dist/nightowl.js"></script>
"""

    links = []

    for details in chat_files_details:
        original_path, sanitized_filename, month_year, _, final_path = details

        with open(original_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        # Insert JS snippet
        link_tag = soup.find('link', {'href': re.compile('https://fonts.googleapis.com/css')})
        if link_tag:
            link_tag.insert_after(BeautifulSoup(js_snippet, 'html.parser'))

        # Update title and add <h1> tag
        if soup.title:
            soup.title.string = sanitized_filename
        body_tag = soup.find('body')
        if body_tag:
            new_h1_tag = soup.new_tag('h1')
            new_h1_tag.string = sanitized_filename
            body_tag.insert(0, new_h1_tag)

        # Directly write modifications to the new path
        if os.path.exists(final_path):
            os.remove(final_path)  # Ensure the file does not already exist

        with open(final_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))

        # Remove the original file to avoid duplicates
        if original_path != final_path:
            os.remove(original_path)

        # Add the link to the list
        links.append(f"<li>../trans/{month_year}/{sanitized_filename}.html</li>")

    # Write the links to the text file
    with open('chat_links.txt', 'w', encoding='utf-8') as file:
        for link in links:
            file.write(f"{link}\n")

if __name__ == "__main__":
    modify_html_files()
