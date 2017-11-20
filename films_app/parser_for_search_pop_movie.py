from datetime import datetime, timedelta
import re
import requests
from multiprocessing.dummy import Pool
from bs4 import BeautifulSoup as bs


IMAGE_FILM_URL = 'http/kinopoisk.ru/images/film_big/{}.jgp'


def get_date_for_search(delta_days):
    current_date = datetime.now().date()
    initial_date = (datetime.now() - timedelta(days=delta_days)).date()
    return current_date, initial_date


def fetch_afisha_page():
    url_afisha = 'https://www.afisha.ru/msk/schedule_cinema/'
    raw_html = requests.get(url_afisha).content
    return raw_html


def fetch_afisha_film_page(link_movie):
    content_film_page = requests.get(link_movie).content
    return content_film_page


def parse_afisha_film_page(link_movie):
    content = bs(fetch_afisha_film_page(link_movie), 'html.parser')
    description_id = {'id':'ctl00_CenterPlaceHolder_ucMainPageContent_pEditorComments'}
    ganres = content.find_all('div', {'class':'b-tags'}, 'a')
    try:
        movie_description = content.find('p', description_id).text.strip()
    except AttributeError:
        movie_discription = None
    return movie_description, ganres[0].text.strip()


def parse_afisha_list(afisha_html, good_count_cinemas):
    content = bs(afisha_html, 'html.parser')
    content_movies = content('div',
                             {'class': 'object s-votes-hover-area collapsed'})
    info_movies_afisha = []
    for movie in content_movies:
        title = movie('h3', {'class': 'usetags'})[0].get_text()
        count_cinemas = len(movie('td',{'class': 'b-td-item'},'a'))
        link_movie = movie.h3.a['href']
        if int(count_cinemas) >= good_count_cinemas:
            description, ganres = parse_afisha_film_page(link_movie)
            title_and_count_cinemas = {'title': title,
                                       'count_cinemas': count_cinemas,
                                       'ganres': ganres,
                                       'description': description}
            info_movies_afisha.append(title_and_count_cinemas)
    return info_movies_afisha


def fetch_movie_info(last_month, current_month):
    url_premiers_of_month = 'https://www.kinopoisk.ru/premiere/ru/2017/month/{}/'
    url_after_scroll = 'page/1/ajax/true/'
    if current_month != last_month:
        last_month_content = requests.get(
            url_premiers_of_month.format(last_month)).content
        last_month_content_scroll = requests.get(
            url_premiers_of_month.format(last_month) +
            url_after_scroll).content
        current_month_content = requests.get(
            url_premiers_of_month.format(current_month)).content
        current_month_content_scroll = requests.get(
            url_premiers_of_month.format(current_month) +
            url_after_scroll).content
        full_content = last_month_content + current_month_content + \
                       current_month_content_scroll + last_month_content_scroll
    else:
        current_month_content = requests.get(
            url_premiers_of_month.format(current_month)).content
        current_month_content_scroll = requests.get(
            url_premiers_of_month.format(current_month) +
            url_after_scroll).content
        full_content = current_month_content + current_month_content_scroll
    return full_content


def get_films_in_kinopoisk(kinopoisk_content,
                           initial_date,
                           current_date,
                           good_rate):
    content = bs(kinopoisk_content, 'html.parser')
    content_movies = content.find_all('div', {'class': 'premier_item'})
    info_movies_kinopoisk = []
    for movie in content_movies:
        title = movie.find('span', {'class': 'name'}).text
        start_date = movie.find('meta').get('content')
        id_movie = movie['id']
        poster_movie = IMAGE_FILM_URL.format(id_movie)
        try:
            rating = movie.find('u').text.split()[0]
        except AttributeError:
            continue
        if re.search('\W.',rating) is None:
            continue
        start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
        if current_date >= start_date >= initial_date and float(rating) >= good_rate:
            title_rate_id = {'title': title, 'rate': rating,
                             'poster': poster_movie}
            info_movies_kinopoisk.append(title_rate_id)
    return info_movies_kinopoisk


def get_pop_movies(list_afisha, list_kinopoisk):
    common_info_list = []
    for movie_afisha in list_afisha:
        for movie_kinopoisk in list_kinopoisk:
            if movie_afisha['title'] == movie_kinopoisk['title']:
                movie_afisha.update(movie_kinopoisk)
                common_info_list.append(movie_afisha)
    print(common_info_list)
    return common_info_list


def output_movies():
    delta_days = 31
    good_rate = 5.00
    good_count_cinemas = 30
    current_date, initial_date = get_date_for_search(delta_days)
    current_month = datetime.today().month
    last_month = initial_date.month
    kinopoisk_content = fetch_movie_info(last_month, current_month)
    list_kinopoisk = get_films_in_kinopoisk(kinopoisk_content,
                                            initial_date,
                                            current_date,
                                            good_rate)
    afisha_content = fetch_afisha_page()
    list_afisha = parse_afisha_list(afisha_content, good_count_cinemas)
    common_info_list = get_pop_movies(list_afisha, list_kinopoisk)
    return common_info_list[:10]


if __name__ == '__main__':
    print(output_movies())