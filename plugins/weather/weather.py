# https://github.com/seriyps/ru_number_to_text - library to translate numbers to text
# используется
import datetime
import random

import pyowm

import pymorphy2
from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon


class Weather(AppDaemon):

    def initialize(self):
        self.context_sensitive = True
        # Create intent
        engine = self.get_app("brain").engine
        self.read_strings = self.get_app("brain").read_dialog_files
        keyword = ["погода", "дождь", "снег"]
        day = ["сегодня", "завтра", "послезавтра", "понедельник", "вторник",
               "среда", "четверг", "пятница", "суббота", "воскресенье"]
        city = ["смоленск", "москва", "мценск",
                "муром", "красноярск", "владимир", "мирный"]
        for k in keyword:
            engine.register_entity(k, "WeatherKeyword")
        for d in day:
            engine.register_entity(d, "WeatherDay")
        for c in city:
            engine.register_entity(c, "WeatherCity")
        # engine.register_regex_entity(" в (?P<WeatherCity>.*)")
        weather_intent = IntentBuilder("weather").require(
            "WeatherKeyword").optionally("WeatherDay").optionally("WeatherCity").build()
        engine.register_intent_parser(weather_intent)

        # Initialize openweathermap parser
        self.owm = pyowm.OWM('', language='ru')

        # Initialize pymorphy
        self.morph = pymorphy2.MorphAnalyzer()

        # Phrases
        self.weather_phrases = self.read_strings("weather.dialog")
        self.weather_now_phrases = self.read_strings("now.dialog")
        self.rain_phrases = self.read_strings("rain.dialog")
        self.no_rain_phrases = self.read_strings("no_rain.dialog")
        self.snow_phrase = self.read_strings("snow.dialog")
        self.no_snow_phrase = self.read_strings("no_snow.dialog")

        self.log("Weather plugin initialized")

    def handle(self, intent_dict):
        day = intent_dict.get("WeatherDay", "сегодня")
        dt = self.get_datetime(day)
        if self.morph.parse(day)[0].inflect({'accs'}) is None:
            sp_day = day
            in_prefix = ""
        else:
            sp_day = self.morph.parse(day)[0].inflect({'accs'})[0]
            in_prefix = "в"

        city = intent_dict.get("WeatherCity", "смоленск")
        if self.morph.parse(city)[0].inflect({'loct'}) is None:
            sp_city = city
        else:
            sp_city = self.morph.parse(city)[0].inflect({'loct'})[0]
        sp_city = sp_city.capitalize()
        request = intent_dict.get("WeatherKeyword")

        forecast = self.owm.daily_forecast(city, limit=7)
        weather = forecast.get_weather_at(dt)

        temp_min = round(weather.get_temperature(unit='celsius')['min'])
        temp_max = round(weather.get_temperature(unit='celsius')['max'])

        status = weather.get_detailed_status()

        wnow = self.owm.weather_at_place(city)
        obs = wnow.get_weather()
        temp_now = round(obs.get_temperature(unit='celsius')['temp'])
        degree_n = self.morph.parse(
            "градус")[0].make_agree_with_number(temp_now).word
        status_now = obs.get_detailed_status()

        if request == "погода":
            speech = random.choice(self.weather_phrases).format(
                day=sp_day, city=sp_city, status=status, temp_min=temp_min, temp_max=temp_max, in_prefix=in_prefix)
            speech = speech[0].capitalize() + speech[1:]
            if day == "сегодня":
                speech = speech + " " + random.choice(self.weather_now_phrases).format(
                    status=status_now, temp_now=temp_now, degree=degree_n)
        elif request == "дождь":
            if forecast.will_be_rainy_at(dt):
                speech = random.choice(self.rain_phrases)
            else:
                speech = random.choice(self.no_rain_phrases)
        elif request == "снег":
            if forecast.will_be_snowy_at(dt):
                speech = random.choice(self.snow_phrase)
            else:
                speech = random.choice(self.no_snow_phrase)

        return speech

    def get_datetime(self, day_str):
        "Get datetime object from string"
        now = datetime.datetime.now()
        daydelta = datetime.timedelta(days=1)
        weekdays = {"понедельник": 0, "вторник": 1, "среда": 2,
                    "четверг": 3, "пятница": 4, "суббота": 5, "воскресение": 6}
        if day_str == "сегодня":
            return now
        elif day_str == "завтра":
            return now + daydelta
        elif day_str in weekdays:
            while now.weekday() != weekdays[day_str]:
                now = now + daydelta
            return now
