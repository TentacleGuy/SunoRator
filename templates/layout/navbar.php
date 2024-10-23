<nav class="uk-navbar-container">
    <div class="uk-container">
        <div uk-navbar>
            <div class="uk-navbar-left">
                <ul class="uk-navbar-nav">
                    {% for page in pages %}
                    <li><a href="{{ url_for(page) }}">{{ page.capitalize() }}</a></li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
</nav>