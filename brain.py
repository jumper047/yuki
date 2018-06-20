
import datetime
import random
import re

import appdaemon.appapi as appapi
import pymorphy2
from adapt.context import ContextManager
from adapt.engine import IntentDeterminationEngine
from appdaemon.appapi import AppDaemon


class Brain(AppDaemon):

    def initialize(self):
        self.morph = pymorphy2.MorphAnalyzer()
        self.engine = IntentDeterminationEngine()
        self.context_managers = {}
        self.last_request = {}

    def query(self, query, connector):
        nquery = self.normalize(query)
        if not self.context_managers.get(connector):
            self.context_managers[connector] = ContextManager()
        if not self.last_request.get(connector):
            self.last_request[connector] = datetime.datetime.now()
        last_rq_delta = datetime.datetime.now() - self.last_request[connector]
        if last_rq_delta.seconds > 300:
            # resetting context, if last conversation was more than 15 minutes
            # ago
            self.context_managers[connector].frame_stack = []
        message = "Прости, что то пошло не так"
        for intent in self.engine.determine_intent(nquery, include_tags=True, context_manager=self.context_managers[connector]):
            # after enabling context management, it can become more important
            if intent and intent.get('confidence') > 0:
                if self.get_app(intent["intent_type"]).context_sensitive:
                    for tag in intent["__tags__"]:
                        context_entity = tag.get('entities')[0]
                        if self.get_app(intent["intent_type"]).context_blacklist\
                                and context_entity['data'][0][1]\
                                in self.get_app(intent["intent_type"]).context_blacklist:
                            continue
                        self.context_managers[
                            connector].inject_context(context_entity)
                message = self.get_app(intent["intent_type"]).handle(intent)
        self.last_request[connector] = datetime.datetime.now()
        # Some code for self-analyze
        self.get_app("analysis").add_entry(connector, intent[
            "intent_type"], query, len(self.context_managers[connector].frame_stack))
        self.get_app(connector).answer(message)

    def normalize(self, text):
        """Remove punctuation, set all words to normal form"""
        nwords = []
        ctext = ""
        punctuation = [",", ".", "!", "?"]
        text = text.lower()
        for s in text:
            if s not in punctuation:
                ctext += s
        for word in ctext.split(' '):
            nword = self.morph.parse(word)[0].normal_form
            nwords.append(nword)
        nwords = " ".join(nwords)
        nwords = self.text_to_number(nwords)
        return nwords

    def text_to_number(self, text):
        """
        Function transform all numbers (0-999 for now) in sentence from text to digits
        """
        numbers = {
            "ноль": 0,
            "один": 1,
            "два": 2,
            "три": 3,
            "четыре": 4,
            "пять": 5,
            "шесть": 6,
            "семь": 7,
            "восемь": 8,
            "девять": 9,
            "десять": 10,
            "одинадцать": 11,
            "двенадцать": 12,
            "тринадцать": 13,
            "четырнадцать": 14,
            "пятнадцать": 15,
            "шестнадцать": 16,
            "семнадцать": 17,
            "восемнадцать": 18,
            "девятнадцать": 19,
            "двадцать": 20,
            "тридцать": 30,
            "сорок": 40,
            "пятьдесят": 50,
            "шестьдесят": 60,
            "семьдесят": 70,
            "восемьдесят": 80,
            "девяносто": 90,
            "сто": 100,
            "двести": 200,
            "триста": 300,
            "четыреста": 400,
            "пятьсот": 500,
            "шестьсот": 600,
            "семьсот": 700,
            "восемьсот": 800,
            "девятьсот": 900,
            "тысяча": 1000
        }
        words = text.split(' ')
        for n in range(0, len(words)):
            if words[n] in numbers:
                n1000 = 0
                n100 = 0
                n20 = 0
                n10 = 0
                n1 = 0
                if numbers[words[n]] < 20:
                    words[n] = str(numbers[words[n]])
                elif 20 <= numbers[words[n]] < 100:
                    n10 = numbers[words[n]]
                    if len(words) >= n + 2 and words[n + 1] in numbers and numbers[words[n + 1]] < 10:
                        n1 = numbers[words[n + 1]]
                        del(words[n + 1])
                    words[n] = str(n10 + n1)
                elif 100 <= numbers[words[n]] < 1000:
                    n100 = numbers[words[n]]
                    if len(words) >= n + 2 and words[n + 1] in numbers and 20 <= numbers[words[n + 1]] < 100:
                        n10 = numbers[words[n + 1]]
                        if len(words) >= n + 3 and words[n + 2] in numbers and 1 <= numbers[words[n + 2]] < 10:
                            n1 = numbers[words[n + 2]]
                            del(words[n + 2])
                        del(words[n + 1])
                    elif len(words) >= n + 2 and words[n + 1] in numbers and 1 <= numbers[words[n + 1]] < 20:
                        n20 = numbers[words[n + 1]]
                        del(words[n + 1])
                    words[n] = str(n100 + n20 + n10 + n1)
                # elif number [word] == 1000:
                #     pass
            if n == len(words) - 1:
                break
        return " ".join(words)

    def read_dialog_files(self, dialog_file):
        """
        Reads file with phrases and returns list of them
        """
        dialog = []
        with open(dialog_file, 'r') as d:
            for line in d:
                dialog.append(line[:-1])
        return dialog

    def my_name(self):
        names = ["Jumper"]
        return random.choice(names)

    def greeting(self):
        phrases = ["Голосовой интерфейс активирован",
                   "%s, я тут!",
                   "Привет, %s!"]
        phrase = random.choice(phrases)
        try:
            return phrase % self.my_name()
        except TypeError:
            return phrase

    def dont_understand(self):
        phrases = ["Прости, %s, я не поняла",
                   "Повтори пожалуйста",
                   "Прости, что?"]
        phrase = random.choice(phrases)
        try:
            return phrase % self.my_name()
        except TypeError:
            return phrase
