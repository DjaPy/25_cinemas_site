from datetime import datetime, timedelta
import re
import requests
import time
from queue import Queue
import threading
from operator import itemgetter
from bs4 import BeautifulSoup as bs


IMAGE_FILM_URL = 'https://st.kp.yandex.net/images/film_big/{}.jpg'
URL_AFISHA = 'https://www.afisha.ru/msk/schedule_cinema/'
URLS_KINOPOISK = ['https://www.kinopoisk.ru/premiere/ru/2017/month/{}/',
                  'https://www.kinopoisk.ru/premiere/ru/2017/month/{}/page/1/ajax/true/']
queue = Queue()


def get_date_for_search(delta_days):
    current_date = datetime.now().date()
    initial_date = (datetime.now() - timedelta(days=delta_days)).date()
    return current_date, initial_date


def fetch_movie_kinopoisk(queue, url):
    queue.put(requests.get(url).content)


def get_threads_kinopoisk(month):
    content_list = []
    for url in URLS_KINOPOISK:
        url = url.format(month)
        thread = threading.Thread(target=fetch_movie_kinopoisk,
                                  args=(queue, url))
        thread.start()
        result_thread = queue.get()
        content_list.append(result_thread)
    content = content_list[0] + content_list[1]
    return content


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


def fetch_afisha_film():
    raw_html = requests.get(URL_AFISHA).content
    return raw_html


def parse_afisha_schedule_cinema(afisha_html, good_count_cinemas):
    content = bs(afisha_html, 'html.parser')
    content_movies = content('div',
                             {'class': 'object s-votes-hover-area collapsed'})
    info_movies_afisha = []
    for movie in content_movies:
        count_cinemas = len(movie('td',{'class': 'b-td-item'},'a'))
        if int(count_cinemas) >= good_count_cinemas:
            info_movies_afisha.append({'count_cinemas': count_cinemas,
                                       'movie_content': movie})
    return info_movies_afisha


def parse_info_movies_afisha(info_movies_afisha):
    data_info_movies = []
    for movie in info_movies_afisha:
        count_cinemas = movie['count_cinemas']
        movie = movie['movie_content']
        title = movie('h3', {'class': 'usetags'})[0].get_text()
        link_movie = movie.h3.a['href']
        film_info = {'title': title,
                      'count_cinemas': count_cinemas,
                      'link': link_movie}
        data_info_movies.append(film_info)
    return data_info_movies


def fetch_afisha_film_page(queue, link_movie):
    queue.put(requests.get(link_movie).content)


def get_threads_afisha(data_info_movies):
    movie_full_info_with_afisha = []

    for movie in data_info_movies:
        url = movie['link']
        thread = threading.Thread(target=fetch_afisha_film_page,
                                  args=(queue, url))
        thread.start()
        content = queue.get()
        content = bs(content, 'html.parser')
        description_id = {
            'id': 'ctl00_CenterPlaceHolder_ucMainPageContent_pEditorComments'}
        ganres = content.find_all('div', {'class': 'b-tags'}, 'a')
        try:
            movie_description = content.find('p', description_id).text.strip()
        except AttributeError:
            movie_discription = None
        movie.update(ganres=ganres[0].text.strip(), description=movie_description)
        movie_full_info_with_afisha.append(movie)
    return movie_full_info_with_afisha


def get_pop_movies(list_afisha, list_kinopoisk):
    common_info_list = []
    for movie_afisha in list_afisha:
        for movie_kinopoisk in list_kinopoisk:
            if movie_afisha['title'] == movie_kinopoisk['title']:
                movie_afisha.update(movie_kinopoisk)
                common_info_list.append(movie_afisha)
    sorted_common_info_list = sorted(common_info_list,
                                     key=itemgetter('rate'),
                                     reverse=True)
    return sorted_common_info_list


def output_movies():
    delta_days = 30
    good_rate = 4.00
    good_count_cinemas = 30
    current_date, initial_date = get_date_for_search(delta_days)
    current_month = datetime.today().month
    last_month = initial_date.month
    if last_month != current_month:
        kinopoisk_content = get_threads_kinopoisk(last_month) + \
                             get_threads_kinopoisk(current_month)
    else:
        kinopoisk_content = get_threads_kinopoisk(current_month)
    kinopoisk_info_list = get_films_in_kinopoisk(kinopoisk_content,
                                                initial_date,
                                                current_date,
                                                good_rate)
    afisha_html = fetch_afisha_film()
    info_movies_afisha = parse_afisha_schedule_cinema(afisha_html,
                                                       good_count_cinemas)
    data_movies_afisha = parse_info_movies_afisha(info_movies_afisha)
    afisha_info_list = get_threads_afisha(data_movies_afisha)
    return get_pop_movies(afisha_info_list, kinopoisk_info_list)[:10]


if __name__ == '__main__':
    delta_days = 31
    good_rate = 5.00
    good_count_cinemas = 30
    current_date, initial_date = get_date_for_search(delta_days)
    current_month = datetime.today().month
    last_month = initial_date.month
    tic = time.time()
    if last_month != current_month:
        kinopoisk_content = get_threads_kinopoisk(last_month) +\
                            get_threads_kinopoisk(current_month)
    else:
        kinopoisk_content = get_threads_kinopoisk(current_month)
    kinopoisk_info_list = get_films_in_kinopoisk(kinopoisk_content,
                                                 initial_date,
                                                 current_date,
                                                 good_rate)
    tac = time.time()
    print(tac - tic)
    tic = time.time()
    afisha_html = fetch_afisha_film()
    info_movies_afisha = parse_afisha_schedule_cinema(afisha_html,
                                                     good_count_cinemas)
    data_movies_afisha = parse_info_movies_afisha(info_movies_afisha)
    afisha_info_list = get_threads_afisha(data_movies_afisha)
    tac = time.time()
    print(tac - tic)
    for movie in get_pop_movies(afisha_info_list, kinopoisk_info_list)[:10]:
        print(movie)