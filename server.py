from flask import Flask, render_template, Response
import tempfile
from werkzeug.contrib.cache import FileSystemCache
from films_app.parser_for_search_pop_movie import output_movies
import json
import logging


ONE_DAY = 60 * 60 * 24

app = Flask(__name__)
tmp_dir = tempfile.mkdtemp()
cache = FileSystemCache(cache_dir=tmp_dir)


def get_films_from_cache():
    films = cache.get('films')
    if films is None:
        films = output_movies()
        cache.set('films', films, timeout=ONE_DAY)
    return films


@app.route('/')
def films_list():
    return render_template('films_list.html', films=get_films_from_cache())


@app.route('/api')
def get_api():
    return Response(json.dumps(get_films_from_cache(),
                               indent=2,
                               ensure_ascii=False),
                    content_type='application/json; charset=utf-8')


if __name__ == "__main__":
    app.run()
