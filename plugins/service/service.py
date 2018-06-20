from random import choice

from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon


class Rest(AppDaemon):

    def initialize(self):

        engine = self.get_app("brain").engine
        keyword = ["отдыхать", "отдохнуть"]
        for k in keyword:
            engine.register_entity(k, "RestKeyword")
        rest_intent = IntentBuilder("rest")\
            .require("RestKeyword")\
            .build()
        engine.register_intent_parser(rest_intent)

        self.ok_phrases = ["Хорошо, дай знать, когда я понадоблюсь.",
                           "Ладно, пойду, отдохну.",
                           "Ок. Пиши, если понадоблюсь",
                           "Хорошо, отключаюсь",
                           "Ок. Если что - пиши в чатик",
                           "Ох, я думала, ты не предложешь. Отключаюсь."]

        print("rest initialized")

    def handle(self, intent_dict):
        self.turn_off("input_boolean.yuki_listener")
        return choice(self.ok_phrases)
