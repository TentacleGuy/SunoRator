import os
from vars import *
from flask import render_template


def get_file_path(folder_name):
    return os.path.join(root_folder, folder_name)
    
def create_routes(app):
    pages = []
    content_folder_path = get_file_path(content_folder)
    
    for filename in os.listdir(content_folder_path):
        if filename.endswith('.php'):
            route_name = filename.split('.')[0]  # Name of the file without extension
            pages.append(route_name)  # Add to the list of pages

            # Function to create the route
            def make_route(route):
                return lambda: render_template(f'content/{route}.php', pages=pages)

            # Add the route to the Flask app
            app.add_url_rule(f'/{route_name}', route_name, make_route(route_name))
    
    return pages




