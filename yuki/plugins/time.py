import datetime
from random import choice

from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon
from pymorphy2 import MorphAnalyzer


class SayTime(AppDaemon):

    def initialize(self):
        self.answers = ["Сейчас {hour} {hword} {minute} {mword}.",
                        "Московское время - {hour} {hword} {minute} {mword}.",
                        "{hour} {hword} {minute} {mword}.",
                        "{hour} {hword} {minute} {mword}."]
        self.morph = MorphAnalyzer()

        engine = self.get_app("brain").engine
        keyword = ["час", "время"]
        question = ["сколько", "который"]
        for k in keyword:
            engine.register_entity(k, "SayTimeKeyword")
        for q in question:
            engine.register_entity(q, "SayTimeQuestion")
        saytime_intent = IntentBuilder("saytime").\
            require("SayTimeKeyword").optionally("SayTimeQuestion").build()
        engine.register_intent_parser(saytime_intent)

        print("saytime init done")

    def handle(self, intent_dict):
        now = datetime.datetime.now()
        hword = "час"
        ahword = self.morph.parse(
            hword)[0].make_agree_with_number(now.hour).word
        mword = "минута"
        amword = self.morph.parse(
            mword)[0].make_agree_with_number(now.minute).word
        return choice(self.answers).format(hour=now.hour, minute=now.minute, hword=ahword, mword=amword)
