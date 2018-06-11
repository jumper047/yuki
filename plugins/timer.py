import datetime
import threading
from random import choice

from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon
from pymorphy2 import MorphAnalyzer


class Timer(AppDaemon):

    def initialize(self):

        self.morph = MorphAnalyzer()

        self.ok_phrases = ["Без проблем, таймер сработает через {time}",
                           "Ок, таймер сработает через {time}",
                           "Сделано, таймер сработает через {time}",
                           "Готово, сработает через {time}",
                           "Ставлю таймер на {time}",
                           "Таймер на {time} - сделано"]

        self.remaining_phrases = ["Осталось {remain}.",
                                  "Таймер сработает через {remain}.",
                                  "{remain} до конца."]

        self.not_set_phrases = ["Таймер не установлен.",
                                "Я не засекала.",
                                "Прости, я не засекала.",
                                "Таймер? Не знаю. Не засекала."]

        self.already_set_phrases = ["Таймер уже установлен.",
                                    "Ты уже поставил таймер."]

        self.ok_remove_phrases = ["Отменяю.",
                                  "Хорошо, таймер отключен.",
                                  "Таймер выключен"]

        self.timer_ended_phrases = ["Время вышло!",
                                    "Сработал таймер",
                                    "Время!"]

        engine = self.get_app("brain").engine
        keyword = ["таймер", "таймеры"]
        self.set_timer_words = ["поставить", "установить"]
        self.reset_timer_words = ["сбросить", "отменить", "остановить"]
        self.state_timer_words = ["как", "остаться", "состояние"]
        re_hours = "(?P<TimerHours>[0-9]+) (час|часы)"
        re_minutes = "(?P<TimerMinutes>[0-9]+) минута"
        re_seconds = "(?P<TimerSeconds>[0-9]+) секунда"
        for k in keyword:
            engine.register_entity(k, "TimerKeyword")
        for a in self.set_timer_words:
            engine.register_entity(a, "TimerAction")
        for a in self.reset_timer_words:
            engine.register_entity(a, "TimerAction")
        for a in self.state_timer_words:
            engine.register_entity(a, "TimerAction")
        engine.register_regex_entity(re_hours)
        engine.register_regex_entity(re_minutes)
        engine.register_regex_entity(re_seconds)
        timer_intent = IntentBuilder("timer")\
            .require("TimerKeyword")\
            .optionally("TimerAction")\
            .optionally("TimerHours")\
            .optionally("TimerMinutes")\
            .optionally("TimerSeconds")\
            .build()
        engine.register_intent_parser(timer_intent)

        self.context_sensitive = True
        self.context_blacklist = ["TimerHours", "TimerSeconds", "TimerMinutes"]

        self.timer_handler = threading.Timer(10, self.timer_ended)

        print("timer initialized")

    def handle(self, intent_dict):
        action = intent_dict.get("TimerAction", "cостояние")
        # if "TimerHours" in intent_dict or "TimerMinutes" in intent_dict or "TimerSeconds" in intent_dict:
        # action = "поставить"
        if action in self.set_timer_words:
            print("setting timer")
            return self.start_timer(intent_dict)
        elif action in self.reset_timer_words:
            print("stopping timer")
            return self.stop_timer()
        elif action in self.state_timer_words:
            print("getting state")
            return self.state_timer()
        else:
            return "Прости, что то не так пошло с этим таймером"

    def start_timer(self, intent_dict):
        if self.timer_handler.is_alive():
            return choice(self.already_set_phrases)
        hours = int(intent_dict.get("TimerHours", 0))
        print("hours:", hours)
        minutes = int(intent_dict.get("TimerMinutes", 0))
        print("minutes:", minutes)
        seconds = int(intent_dict.get("TimerSeconds", 0))
        print("seconds:", seconds)
        time = hours * 3600 + minutes * 60 + seconds
        self.timer_handler = threading.Timer(time, self.timer_ended)
        self.timer_handler.start()
        self.timer_end_time = datetime.datetime.now() + datetime.timedelta(seconds=time)
        print(self.timer_handler.is_alive())
        return choice(self.ok_phrases).format(time=self.pron_time(hours, minutes, seconds))

    def state_timer(self):
        if not self.timer_handler.is_alive():
            return choice(self.not_set_phrases)
        timer_delta = self.timer_end_time - datetime.datetime.now()
        hours, secs = divmod(timer_delta.seconds, 3600)
        minutes, seconds = divmod(secs, 60)
        return choice(self.remaining_phrases).format(remain=self.pron_time(hours, minutes, seconds))

    def stop_timer(self):
        if self.timer_handler is None:
            return choice(self.not_set_phrases)
        self.timer_handler.cancel()
        return choice(self.ok_remove_phrases)

    def timer_ended(self):
        print("Timer!!!")
        # yandex tts say some phrase

    def pron_time(self, hours, minutes, seconds):
        phours = str(hours) + " " + self.morph.parse("час")[
            0].make_agree_with_number(hours).word if hours > 0 else ""
        pminutes = str(minutes) + " " + self.morph.parse("минута")[
            0].make_agree_with_number(minutes).word if minutes > 0 else ""
        pseconds = str(seconds) + " " + self.morph.parse("секунда")[
            0].make_agree_with_number(seconds).word if seconds > 0 else ""
        return " ".join([phours, pminutes, pseconds])
