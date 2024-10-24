import os
from vars import *
from flask import render_template

#app
def get_file_path(folder_name):
    return os.path.join(root_folder, folder_name)
    
def create_routes(app):
    pages = []
    content_folder_path = get_file_path(content_folder)
    
    for filename in os.listdir(content_folder_path):
        if filename.endswith('.php'):
            # Split filename to get the order and the actual route name
            parts = filename.split('-')
            route_name = parts[1].split('.')[0]  # The route name without the extension
            
            # Add the cleaned route name to the list of pages for the menu
            pages.append(route_name)
            
            # Function to create the route, using the actual filename for the content
            def make_route(route):
                return lambda: render_template(f'content/{route}.php', pages=pages)

            # Add the URL rule without the number in the path
            app.add_url_rule(f'/{route_name}', route_name, make_route(filename.split('.')[0]))
    
    return pages



