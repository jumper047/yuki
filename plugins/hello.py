from adapt.intent import IntentBuilder
from appdaemon.appapi import AppDaemon


class Hello(AppDaemon):

    def initialize(self):
        self.context_sensitive = False
        engine = self.get_app("brain").engine
        keyword = ["привет", "пока"]
        for k in keyword:
            engine.register_entity(k, "HelloKeyword")

        hello_intent = IntentBuilder("hello").require(
            "HelloKeyword").build()

        engine.register_intent_parser(hello_intent)

        print("hello initialized")

    def handle(self, intent_dict):
        if intent_dict["HelloKeyword"] == "привет":
            speech = "Здравствуй"
        else:
            speech = "До скорого!"
        return speech

    def check(self, query, tquery):
        return bool("погода" in tquery)
