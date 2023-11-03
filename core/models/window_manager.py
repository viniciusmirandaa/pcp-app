from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivy.lang import Builder
from login import TelaLogin
from login import SenhaCard
from login import ButtonFocus


class LoginScreen(Screen):
    login = TelaLogin()
    login.on_release()

class WorkProductionScreen(Screen):
    pass


class WindowManager(ScreenManager):
    pass


class PcpApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__()
        self.second_screen = WorkProductionScreen()
        self.first_screen = LoginScreen()
        self.screen_manager = ScreenManager()

    def build(self):
        self.theme_cls.primary_palette = 'Purple'
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_hue = "700"
        return Builder.load_file('core/views/window_manager.kv')

    def change_screen(self, menu):
        self.screen_manager.switch_to(menu)


PcpApp().run()
