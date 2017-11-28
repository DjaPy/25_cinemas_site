# Cinemas Site

The website displays the following information for popular films from the site [Afisha](https://afisha.ru) and [Kinopoisk](https://kinopoisk.ru):

- Poster 
- Title
- Gеnres
- Description
- Rating
- Count cinemas

View [website](https://telegraph-story.herokuapp.com/)

Bonus: provides an API in JSON format

# What's inside

The application is deployed on [heroku](https://heroku.com) using Flask framework.

# Run locally

Use Venv or virtualenv for insulation project. Virtualenv example:

```
$ python virtualevn myenv
$ source myenv/bin/activate
```

Install requirements:

```
pip install -r requirements.txt
```
Run gunicorn:

At the root of the project
```
gunicorn server:app
```
and simple [click](http://localhost:8000)


# Project Goals

The code is written for educational purposes. Training course for web-developers - [DEVMAN.org](https://devman.org)
