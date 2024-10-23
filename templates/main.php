<!DOCTYPE html>
<html lang="de">
    <head>
        <title>Suno KIt</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        
        <!-- CSS -->
        <link rel="stylesheet" href="{{ url_for('static', filename='dist/css/uikit.min.css') }}">
        <link rel="stylesheet" href="{{ url_for('static', filename='dist/css/style.min.css') }}">
    
        <!--- JS -->
        <script src="{{ url_for('static', filename='dist/js/uikit.min.js') }}" defer></script>
        <script src="{{ url_for('static', filename='dist/js/uikit-icons.min.js') }}" defer></script>
    </head>
    <body>
        {% include 'layout/navbar.php' %}

        <!-- Main Content -->
        <div class="uk-container uk-margin">
            {% block content %}{% endblock %}
        </div>

        {% include 'layout/footer.php' %}
    </body>

</html>

<!-- TODO: Sidebar / Modal hinzufügen -->