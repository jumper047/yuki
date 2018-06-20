from random import choice, randint
from time import sleep

import requests

from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon
from pymorphy2 import MorphAnalyzer


class LightControl(AppDaemon):

    def initialize(self):
        self.context_sensitive = True
        engine = self.get_app("brain").engine
        keyword = ["включить", "выключить"]
        scene = ["свет", "подсветка", "лампа"]
        for k in keyword:
            engine.register_entity(k, "LightControlKeyword")
        for s in scene:
            engine.register_entity(s, "LightControlScene")
        lightcontrol_intent = IntentBuilder("lightcontrol")\
            .require("LightControlKeyword")\
            .require("LightControlScene")\
            .build()
        engine.register_intent_parser(lightcontrol_intent)

        self.ok_phrases = ["Ок", "Сделано", "Готово"]

    def handle(self, intent_dict):
        action = intent_dict.get("LightControlKeyword")
        scene = intent_dict.get("LightControlScene")

        if action == "включить" and scene == "свет":
            on = ["light.lustre1", "light.lustre2"]
            off = ["light.bed_lamp", "light.cupboard_lamp"]
            self.batch_switch(on, off)
        elif action == "включить" and scene == "подсветка":
            on = ["light.lustre1", "light.lustre2"]
            off = ["light.bed_lamp", "light.cupboard_lamp"]
            self.batch_switch(off, on)
        elif action == "выключить" and scene == "свет":
            off = ["light.lustre1", "light.lustre2",
                   "light.bed_lamp", "light.cupboard_lamp"]
            on = []
            self.batch_switch(on, off)
        elif action == "выключить" and scene == "лампа":
            self.turn_off("light.table_lamp")
        elif action == "включить" and scene == "лампа":
            self.turn_on("light.table_lamp")
        else:
            return "Что то пошло не так"

        # if randint(0, 9) > 1:
        #     return ""
        # else:
        #     return choice(self.ok_phrases)
        return ""

    def batch_switch(self, on, off):
        for entity in on:
            if self.get_state(entity) == "on":
                continue
            self.turn_on(entity)
            sleep(0.5)

        for entity in off:
            if self.get_state(entity) == "off":
                continue
            self.turn_off(entity)
            sleep(0.5)


class WhoIsAtHome(AppDaemon):
    """Tells, who is at home now"""

    def initialize(self):

        engine = self.get_app("brain").engine
        keyword = ["дом", "квартира"]
        people = ["кто", "брат"]
        for k in keyword:
            engine.register_entity(k, "WhoIsAtHomeKeyword")
        for p in people:
            engine.register_entity(p, "WhoIsAtHomePeople")
        whoisathome_intent = IntentBuilder("whoisathome")\
            .require("WhoIsAtHomeKeyword")\
            .optionally("WhoisAtHomePeople")\
            .build()
        engine.register_intent_parser(whoisathome_intent)

    def handle(self, intent_dict):
        return None

class TurnOnOff(AppDaemon):

    def initialize(self):
        self.entities = {"ноутбук": "switch.laptop",
                         "пылесос": "script.roomba_clean"}

        engine = self.get_app("brain").engine
        keyword = ["включать", "выключать", "включить", "выключить"]
        entity_keyword = ["пылесос", "ноутбук"]
        for k in keyword:
            engine.register_entity(k, "TurnOnOffKeyword")
        for e in entity_keyword:
            engine.register_entity(e, "TurnOnOffEntity")
        turnonoff_intent = IntentBuilder("turnonoff")\
            .require("TurnOnOffKeyword")\
            .require("TurnOnOffEntity")\
            .build()
        engine.register_intent_parser(turnonoff_intent)
        print("turnonoff initialized")

    def handle(self, intent_dict):
        entity = intent_dict["TurnOnOffEntity"]
        action = intent_dict["TurnOnOffKeyword"]
        if "выкл" in action:
            self.turn_off(self.entities[entity])
        else:
            self.turn_on(self.entities[entity])
        return ""
