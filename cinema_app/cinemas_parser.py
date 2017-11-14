from datetime import datetime, timedelta
import re
import requests
from bs4 import BeautifulSoup as bs
from argparse import ArgumentParser


def get_parser_of_command_line():
    parser = ArgumentParser(description='Settings search movies')

    parser.add_argument('-d', '--day', nargs='?',
                        help='The number of days in cinemas',
                        default=21, type=int)
    parser.add_argument('-c', '--count', nargs='?',
                        help='The number of cinemas which show the film',
                        default=30, type=int)
    parser.add_argument('-r', '--rating', nargs='?',
                        help='Minimal movie rating',
                        default=3.00, type=float)
    return parser.parse_args()


def get_date_for_search(delta_days):
    current_date = datetime.now().date()
    initial_date = (datetime.now() - timedelta(days=delta_days)).date()
    return  current_date, initial_date


def fetch_afisha_page():
    url_afisha = 'https://www.afisha.ru/msk/schedule_cinema/'
    raw_html = requests.get(url_afisha).content
    return raw_html


def parse_afisha_list(afisha_html, good_count_cinemas):
    content = bs(afisha_html, 'html.parser')
    content_movies = content('div',
                             {'class': 'object s-votes-hover-area collapsed'})
    info_movies_afisha = []
    for movie in content_movies:
        title = movie('h3', {'class': 'usetags'})[0].get_text()
        count_cinemas = len(movie('td',{'class': 'b-td-item'},'a'))
        if int(count_cinemas) >= good_count_cinemas:
            title_and_count_cinemas = {'title': title,
                                       'count_cinemas': count_cinemas}
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
        try:
            rating = movie.find('u').text.split()[0]
        except AttributeError:
            continue
        if re.search('\W.',rating) is None:
            continue
        start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
        if current_date >= start_date >= initial_date and float(rating) >= good_rate:
            title_and_rate = {'title': title, 'rate': rating}
            info_movies_kinopoisk.append(title_and_rate)
    return info_movies_kinopoisk


def get_pop_movies(list_afisha, list_kinopoisk):
    common_info_list = []
    for movie_afisha in list_afisha:
        for movie_kinopoisk in list_kinopoisk:
            if movie_afisha['title'] == movie_kinopoisk['title']:
                movie_afisha.update(movie_kinopoisk)
                common_info_list.append(movie_afisha)
    return common_info_list


def output_movies_to_console(common_info_list):
    for film in common_info_list[:10]:
        movie = 'Film: {title}'.format(**film)
        rate = 'Kinopoisk rating: {rate}'.format(**film)
        count_cinemas = 'Show in {count_cinemas} cinemas in Moscow'.format(**film)
        print(movie)
        print(rate)
        print(count_cinemas + '\n')


if __name__ == '__main__':
    user_settings = get_parser_of_command_line()
    delta_days = user_settings.day
    good_rate = user_settings.rating
    good_count_cinemas = user_settings.count
    current_date, initial_date = get_date_for_search(delta_days)
    current_month = datetime.today().month
    last_month = initial_date.month
    kinopoisk_content = fetch_movie_info(last_month,current_month)
    list_kinopoisk = get_films_in_kinopoisk(kinopoisk_content,
                                            initial_date,
                                            current_date,
                                            good_rate)
    afisha_content = fetch_afisha_page()
    list_afisha = parse_afisha_list(afisha_content, good_count_cinemas)
    movies_list = get_pop_movies(list_afisha, list_kinopoisk)
    output_movies_to_console(movies_list)