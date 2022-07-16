import feedparser
from flask import Flask,render_template,request,make_response
import datetime

import json
from urllib.request import urlopen
import urllib
import urllib.parse

app = Flask(__name__)
open_weather_key = 'c2f0a56ed6bee405add4389597141e73'
open_exchange_key = '55e2c7c5231f4c6e98abb1d227b1e4b5'

WEATHER_URL  = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=' + open_weather_key
CURRENCY_URL = 'https://openexchangerates.org/api/latest.json?app_id=' + open_exchange_key
DEFAULTS = {'publication':'bbc',
            'city': 'London,UK',
            'currency_from':'GBP',
            'currency_to':'USD',
            }
RSS_FEEDS = {'bbc':'http://feeds.bbci.co.uk/news/rss.xml',
            'cnn':'http://rss.cnn.com/rss/edition.rss',
            'fox':'http://feeds.foxnews.com/foxnews/latest',
            'iol':'http://www.iol.co.za/cmlink/1.640'
             }

def get_news(query):
    if not query or query.lower() not in RSS_FEEDS:
        publication = DEFAULTS["publication"]
    else:
        publication = query.lower()
    feed = feedparser.parse(RSS_FEEDS[publication])
    return feed['entries']


def get_weather(query):
    query = urllib.parse.quote(query)
    url = WEATHER_URL.format(query)
    data = urlopen(url).read()
    parsed = json.loads(data)
    weather = None
    if parsed.get('weather'):
        weather = { 'description':parsed['weather'][0]['description'],
                    'temperature':parsed['main']['temp'],
                    'city':parsed['name'],
                    'country': parsed['sys']['country'],
        }
    return weather


def get_rate(frm, to):
    all_currency = urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get('rates')
    from_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return (to_rate / from_rate, parsed.keys())


def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)


@app.route("/")
def home():
    # get customised headlines, based on user input or default
    publication = get_value_with_fallback("publication")
    articles = get_news(publication)
    # get customised weather based on user input or default
    city = get_value_with_fallback("city")
    weather = get_weather(city)
    # get customised currency based on user input or default
    currency_from = get_value_with_fallback("currency_from")
    currency_to = get_value_with_fallback("currency_to")
    rate, currencies = get_rate(currency_from, currency_to)
    # save cookies and return template
    response = make_response(render_template("home.html",
                                             pub=publication.upper(),
                                             articles=articles,
                                             weather=weather, currency_from=currency_from,
                                             currency_to=currency_to, rate=rate,
                                             currencies=sorted(currencies)))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("publication", publication,
                        expires=expires)
    response.set_cookie("city", city, expires=expires)
    response.set_cookie("currency_from",
                        currency_from, expires=expires)
    response.set_cookie("currency_to",
                        currency_to, expires=expires)
    return response


if __name__ == "__main__":
    app.run(port=5000, debug=True)