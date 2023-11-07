import playwright.sync_api as sync_api
from pydub import AudioSegment
from os import remove
from urllib.request import urlretrieve
import speech_recognition as sr


class SyncRecaptchaResolver:

    def __init__(self):
        self.__timeout = 2000
        self.__recaptcha_iframe = None
        self.__bframe = None

    def __recaptcha_iframe_acnhor_click(self, page: sync_api.Page):
        recaptcha_iframe_name = page.locator("iframe[title='reCAPTCHA']").get_attribute("name")
        self.__recaptcha_iframe = page.frame(name=recaptcha_iframe_name)
        self.__recaptcha_iframe.click('//*[@id="recaptcha-anchor"]/div[1]')

    def __bframe_audio_button_click(self, page):
        recaptcha_bframe_name = page.locator(
            "//iframe[contains(@src,'https://www.google.com/recaptcha/api2/bframe?')]"
        ).get_attribute("name")

        bframe = page.frame(name=recaptcha_bframe_name)
        bframe.click("#recaptcha-audio-button")

        self.__bframe = bframe

    def __get_bframe_audio_source(self, ) -> str:
        audio_source = self.__bframe.locator("#audio-source").get_attribute("src")
        return audio_source

    def __enter_response(self, text: str):
        self.__bframe.locator("#audio-response").press_sequentially(text=text, delay=10)

    def __click_verify_button(self):
        self.__bframe.click("#recaptcha-verify-button")

    def __save_audio_source(self, src):
        urlretrieve(src, "audio.mp3")
        mp3_file = AudioSegment.from_mp3("audio.mp3")
        mp3_file.export("audio.wav", format="wav")
        remove("audio.mp3")

    def __recognize_text_from_audio_source(self):
        recognizer = sr.Recognizer()

        with sr.AudioFile("audio.wav") as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
            except Exception as e:
                raise e

        remove("audio.wav")
        return text

    def sync_resolve(self, page: sync_api.Page):
        try:
            page.wait_for_timeout(timeout=self.__timeout)
            self.__recaptcha_iframe_acnhor_click(page)

            page.wait_for_timeout(timeout=self.__timeout)

            self.__bframe_audio_button_click(page)
            audio_source = self.__get_bframe_audio_source()
            self.__save_audio_source(audio_source)
            text = self.__recognize_text_from_audio_source()
            self.__enter_response(text)

            page.wait_for_timeout(timeout=self.__timeout)
            self.__click_verify_button()

            self.__recaptcha_iframe.wait_for_selector(
                selector=".recaptcha-checkbox-checked", timeout=3000)

        except Exception as e:
            return e
