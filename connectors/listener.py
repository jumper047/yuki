import base64
import os
import sys
import tempfile
import threading
import wave

import speech_recognition as sr
from pocketsphinx import pocketsphinx

import appdaemon.appapi as appapi
import snowboydetect as sd


class MicrophoneInput(appapi.AppDaemon):

    def initialize(self):
        self.microphone_init()
        self.snowboy_yuki_init()
        self.snowboy_prefix_init()
        self.pocketsphinx_init()

        # Home Assistant controls
        self.listen_state(self.toggle_listener,
                          "input_boolean.yuki_listener")

        self.listen_state(self.set_snowboy_yuki_sensitivity,
                          "input_slider.yuki_hotword_sensitivity")
        self.listen_state(self.set_snowboy_prefix_sensitivity,
                          "input_slider.yuki_prefix_hotword_sensitivity")
        self.listen_state(self.set_recognizer, "input_select.yuki_translator")

        self.recognizer = self.get_state("input_select.yuki_translator")
        self.recognize_keyword = self.get_state("input_boolean.yuki_listener")

        self.listening = True
        self.listener_handler = threading.Thread(target=self.listener)
        self.listener_handler.daemon = True
        self.listener_handler.start()

    def microphone_init(self):
        """Initialize microphone and recognizer instances"""
        self.rec = sr.Recognizer()
        self.mic = sr.Microphone()
        self.rec.dynamic_energy_ratio = 2.0  # reduces long false records
        with self.mic as source:
            self.rec.adjust_for_ambient_noise(source)
        self.log("Microphone init done")

    def pocketsphinx_init(self):
        """Initialize pocketsphinx stt engine"""
        language_directory = self.args["pocketsphinx_dir"]
        acoustic_parameters_directory = os.path.join(
            language_directory, "acoustic-model")
        language_model_file = os.path.join(
            language_directory, "language-model.lm.bin")
        phoneme_dictionary_file = os.path.join(
            language_directory, "pronounciation-dictionary.dict")
        config = pocketsphinx.Decoder.default_config()
        config.set_string("-hmm", acoustic_parameters_directory)
        config.set_string("-lm", language_model_file)
        config.set_string("-dict", phoneme_dictionary_file)
        config.set_string("-logfn", os.devnull)
        self.sphinx_decoder = pocketsphinx.Decoder(config)
        self.log("Pocketsphinx init done")

    def snowboy_yuki_init(self):
        """Initialize snowboy hotword detection engine"""
        self.log("Snowboy hotword detector init")
        decoder_model = self.args["snowboy_yuki_mdl"]
        resource_file = self.args["snowboy_res"]
        audio_gain = 1
        sensitivity = "0.4"
        self.snowboy_yuki_decoder = sd.SnowboyDetect(
            resource_filename=resource_file.encode(), model_str=decoder_model.encode())
        self.snowboy_yuki_decoder.SetAudioGain(audio_gain)
        self.snowboy_yuki_decoder.SetSensitivity(sensitivity.encode())
        self.log("\nDecoder: %s\nResource: %s\nAudio gain: %s\nSensitivity: %s" % (
            decoder_model, resource_file, audio_gain, sensitivity))
        self.log("Snowboy hotword detector init done")

    def set_snowboy_yuki_sensitivity(self, entity, attribute, old, new, strange, **kwargs):
        self.snowboy_yuki_decoder.SetSensitivity(str(new).encode())
        new_sens = self.snowboy_yuki_decoder.GetSensitivity()
        print("hotword sens set to {}".format(str(new_sens)))

    def snowboy_prefix_init(self):
        """Initialize snowboy hotword detection engine"""
        self.log("Snowboy hotword detector init")
        decoder_model = self.args["snowboy_hey_mdl"]
        resource_file = self.args["snowboy_res"]
        audio_gain = 1
        sensitivity = "0.45"
        self.snowboy_prefix_decoder = sd.SnowboyDetect(
            resource_filename=resource_file.encode(), model_str=decoder_model.encode())
        self.snowboy_prefix_decoder.SetAudioGain(audio_gain)
        self.snowboy_prefix_decoder.SetSensitivity(
            sensitivity.encode())
        self.log("\nDecoder: %s\nResource: %s\nAudio gain: %s\nSensitivity: %s" % (
            decoder_model, resource_file, audio_gain, sensitivity))
        self.log("Snowboy hotword detector init done")

    def set_snowboy_prefix_sensitivity(self, entity, attribute, old, new, strange, **kwargs):
        self.snowboy_prefix_decoder.SetSensitivity(str(new).encode())
        new_sens = self.snowboy_prefix_decoder.GetSensitivity()

    def toggle_listener(self, entity, attribute, old, new, strange, **kwargs):
        self.recognize_keyword = new

    def set_recognizer(self, entity, attribute, old, new, strange, **kwargs):
        self.recognizer = new

    def answer(self, message):
        self.call_service(self.args["tts"],
                          message=message)

    def listener(self):
        """Speech listening and recognition loop"""
        self.log('Listener started')
        # Record hotword
        while self.listening:
            try:
                with self.mic as source:
                    audio = self.rec.listen(source)
            except OSError:
                self.listening = False

            # Check, if engine is active or not
            if self.recognize_keyword != "on":
                continue

            data = audio.get_raw_data(convert_rate=16000, convert_width=2)
            seconds = len(data) / 32000

            # Hotword detection
            self.snowboy_yuki_decoder.Reset()
            yuki = self.snowboy_yuki_decoder.RunDetection(data)
            if yuki > 0:
                self.snowboy_prefix_decoder.Reset()
                hey = self.snowboy_prefix_decoder.RunDetection(data)
                if hey <= 0:
                    continue
            else:
                continue

            # Trying to switch recognizer
            self.set_state("input_select.yuki_translator", state="internal")

            # Record command
            with self.mic as source:
                self.turn_on("script.low_beep")
                try:
                    audio = self.rec.listen(source, 3)
                except sr.WaitTimeoutError:
                    self.turn_on("script.listening")
                    continue

            data = audio.get_raw_data(convert_rate=16000, convert_width=2)
            seconds = len(data) / 32000

            if self.recognizer == "external":
                # Send data to recognizer
                audio_bytes = base64.b64encode(data)
                audio_string = audio_bytes.decode('utf-8')
                self.fire_event("VOICE_RECORDED",
                                sender="microphone_input", data=audio_string)
                print('audio sended to recognizer')

            elif self.recognizer == "internal":
                print("beginning local recognizer")
                self.sphinx_decoder.start_utt()
                self.sphinx_decoder.process_raw(data, False, True)
                self.sphinx_decoder.end_utt()
                hypothesis = self.sphinx_decoder.hyp()
                print("utterance recognized")
                if hypothesis is not None:
                    print(hypothesis.hypstr)
                    self.get_app("brain").query(
                        hypothesis.hypstr, "microphone_input")


class TranslateHandler(appapi.AppDaemon):

    def initialize(self):
        self.receive_translation = self.listen_event(
            self.retranslate_text, event="SPEECH_RECOGNIZED")

    def retranslate_text(self, event_name, data, kwargs):
        self.get_app("brain").query(data['utterance'], data['sender'])
