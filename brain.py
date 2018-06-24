
import datetime
import random
import re

import appdaemon.appapi as appapi
import pymorphy2
from adapt.context import ContextManager
from adapt.engine import IntentDeterminationEngine
from appdaemon.appapi import AppDaemon
from brain_helpers import text_to_number


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
        text = re.sub('\?|\!|\.|\,', '', text).lower()
        for word in text.split(' '):
            nword = self.morph.parse(word)[0].normal_form
            nwords.append(nword)
        nwords = " ".join(nwords)
        nwords = text_to_number(nwords)
        return nwords

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
