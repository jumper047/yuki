from random import choice

import requests

from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon


class FindPhone(AppDaemon):

    def initialize(self):
        self.context_sensitive = False
        self.answers = ["Хорошо, сейчас позвоню на него.",
                        "Сейчас он начнёт пищать. Ищи!",
                        "Ладно, попробую помочь.",
                        "Ок, я попробую",
                        "Хорошо, сейчас включу пищалку"]

        engine = self.get_app("brain").engine
        keyword = ["телефон", "смартфон"]
        question = ["где", "найти"]
        for k in keyword:
            engine.register_entity(k, "FindPhoneKeyword")
        for q in question:
            engine.register_entity(q, "FindPhoneQuestion")
        findphone_intent = IntentBuilder("findphone").\
            require("FindPhoneKeyword").require("FindPhoneQuestion").build()
        engine.register_intent_parser(findphone_intent)

        print("findphone init done")

    def handle(self, intent_dict):
        requests.get('https://autoremotejoaomgcd.appspot.com/sendmessage?key=APA91bFXqdAorFgm1pxPddXuEbyQXgrwP5lGru1JjoJHEO5OL6u0ctDPJiKtAymtAdVR60xuPJpFE2hO6QARa1uuSJoOTdOL16PIBBTXNreWU1nlAoN_4H6MMHgFocHtWvfsmDqmTm7x&message=find_phone&password=labirintofjumper047')
        return choice(self.answers)
