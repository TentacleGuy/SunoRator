import os
from config.vars import *

#app
def get_file_path(folder_name):
    return os.path.join(root_folder, folder_name)
    
def get_pages():
    pages = []
    content_folder_path = get_file_path(content_folder)
    
    for filename in os.listdir(content_folder_path):
        if filename.endswith('.php'):
            # Split filename to get the order and the actual route name
            parts = filename.split('-')
            order = parts[0]
            name = parts[1].split('.')[0]  # The route name without the extension
            extension = parts[1].split('.')[1]
            url = "content/" + order + "-" + name + "." + extension
            
            # Add a tuple with the URL and cleaned route name to the list of pages
            pages.append((url, name))
    
    return pages






