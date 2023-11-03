from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import FloatLayout
from kivymd.uix.behaviors.focus_behavior import FocusBehavior
from kivy.uix.screenmanager import Screen, ScreenManager
import requests
import json

global uid, session_id


class SenhaCard(MDCard):
    def fechar(self):
        self.parent.remove_widget(self)


class TelaLogin(FloatLayout):

    def abrir_card(self):
        self.add_widget(SenhaCard())

    def login(self, email, senha):
        user_session_data = {
            "jsonrpc": "2.0",
            "params": {
                "db": "mrp",
                "login": email,
                "password": senha
            }
        }
        request = requests.post(url="http://localhost:8069/web/session/authenticate",
                                data=json.dumps(user_session_data).encode(),
                                headers={"Content-Type": "application/json"})
        uid = json.loads(request.content.decode()).get("result").get("uid")
        session_id = request.cookies._cookies.get("localhost.local").get("/").get("session_id").value

    def on_release(self, email, senha, menu):
        login = TelaLogin()
        login.login(email, senha)
        self.change_screen(menu)


class ButtonFocus(MDRaisedButton, FocusBehavior):
    ...
