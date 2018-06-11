import datetime
from random import choice

from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon
from pymorphy2 import MorphAnalyzer


class SayWeekday(AppDaemon):

    def initialize(self):
        self.context_sensitive = True
        self.answers = ["{now} {weekday}.",
                        "{weekday}.",
                        "{weekday} вроде бы."]
        self.times = {"сегодня": 0, "завтра": 1, "послезавтра": 2}

        self.morph = MorphAnalyzer()

        engine = self.get_app("brain").engine
        keyword = ["день", "число"]
        day = ["сегодня", "завтра", "послезавтра"]
        question = ["какой"]
        for k in keyword:
            engine.register_entity(k, "SayWeekdayKeyword")
        for d in day:
            engine.register_entity(d, "SayWeekdayDay")
        for q in question:
            engine.register_entity(q, "SayWeekdayQuestion")
        sayweekday_intent = IntentBuilder("sayweekday").\
            require("SayWeekdayKeyword").optionally(
                "SayWeekdayDay").optionally("SayWeekdayQuestion").build()
        engine.register_intent_parser(sayweekday_intent)

        print("sayweekday initialized")

    def handle(self, intent_dict):
        offset = intent_dict.get("SayWeekdayDay", "сегодня")
        action = intent_dict["SayWeekdayKeyword"]
        mydate = datetime.datetime.now() + \
            datetime.timedelta(days=self.times[offset])
        if action == "день":
            res = self.weekday(mydate)
        else:
            res = self.date(mydate)

        ans = choice(self.answers)
        print(ans)
        print(res)
        print(offset)
        fans = ans.format(weekday=res, now=offset)
        if ans[0] == "{":
            fans = fans.capitalize()
        return fans

    def weekday(self, dt):
        weekdays = {0: "понедельник", 1: "вторник", 2: "среда",
                    3: "четверг", 4: "пятница", 5: "суббота", 6: "воскресение"}
        return weekdays[dt.weekday()]

    def date(self, dt):
        months = {1: "январь",
                  2: "февраль",
                  3: "март",
                  4: "апрель",
                  5: "май",
                  6: "июнь",
                  7: "июль",
                  8: "август",
                  9: "сентябрь",
                  10: "октябрь",
                  11: "ноябрь",
                  12: "декабрь"}
        print(dt.day)
        print(dt.day.__class__)

        return str(dt.day) + " " + self.morph.parse(months[dt.month])[0].make_agree_with_number(dt.day).word
