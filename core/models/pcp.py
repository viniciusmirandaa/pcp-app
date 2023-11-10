from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty
from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.button import MDRoundFlatButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivy.lang import Builder
import requests
import json
import urllib.request
from kivymd.uix.list import ThreeLineIconListItem, IconLeftWidget, ThreeLineListItem
from functools import partial

from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import BaseSnackbar

Window.size = (768, 1024)

URL = "http://%s:%s/jsonrpc" % ('localhost', 8069)
DB = 'mrp'

SERVICE_ORDER_STATE = {
    'pending': 'Aguardando por outra OS',
    'ready': 'Pronto',
    'progress': 'Em Andamento',
    'done': 'Concluído',
    'cancel': 'Cancelado'
}


def json_rpc(url, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
    }
    req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
    if reply.get("error"):
        raise Exception(reply["error"])
    return reply["result"]


def call(service, method, *args):
    return json_rpc(URL, "call", {"service": service, "method": method, "args": args})


class LoginScreen(Screen):
    pass


class SenhaCard(MDCard):
    def fechar(self):
        self.parent.remove_widget(self)


class TelaLogin(FloatLayout):
    screen = ''

    def show_password(self):
        if self.ids.senha.password:
            self.ids.icon_eye.icon = "eye"
            self.ids.senha.password = False
        else:
            self.ids.icon_eye.icon = "eye-off"
            self.ids.senha.password = True

    def set_email_error(self, bool, text=''):
        self.ids.email.error = bool
        self.ids.email.helper_text = text

    def set_senha_error(self, bool, text=''):
        self.ids.senha.error = bool
        self.ids.senha.helper_text = text

    def abrir_card(self):
        self.add_widget(SenhaCard())

    def get_screen(self):
        return self.screen

    def set_screen(self, screen):
        self.screen = screen

    def login(self, email, senha):

        user_session_data = {
            "jsonrpc": "2.0",
            "params": {
                "db": "mrp",
                "login": email,
                "password": senha
            }
        }
        try:
            if not self.ids.email.text and not self.ids.senha.text:
                self.set_senha_error(True, "O email e senha são obrigatórios para verificar a identidade do usuário")
                self.set_email_error(True)
                self.set_screen('login')
                return
            elif not self.ids.email.text:
                self.set_email_error(True, "Este campo é obrigatório")
                self.set_screen('login')
                return
            elif not self.ids.senha.text:
                self.set_senha_error(True, "Este campo é obrigatório")
                self.set_screen('login')
                return
            request = requests.post(url="http://localhost:8069/web/session/authenticate",
                                    data=json.dumps(user_session_data).encode(),
                                    headers={"Content-Type": "application/json"})
            if request.status_code.__eq__(200):
                session = PcpApp.get_running_app()
                session.uid = json.loads(request.content.decode()).get("result").get("uid")
                session.session_id = request.cookies._cookies.get("localhost.local").get("/").get("session_id").value
                session.pwd = senha

                self.set_screen('work_production')
                self.set_email_error(False)
                self.set_email_error(False)
        except requests.exceptions.ConnectionError:
            self.set_email_error(True, "Não foi possível conectar-se ao servidor, relate ao administrador")
            self.set_email_error(True)
            self.set_screen('login')
        except AttributeError:
            self.set_email_error(True, "Email ou senha incorretos")
            self.set_email_error(True)
            self.set_screen('login')


class WorkProductionScreen(Screen):
    pass


class WorkProduction(FloatLayout, HoverBehavior):

    def change_to_os_screen(self, instance):
        self.ids.id_text_field.text = instance.id
        session = PcpApp.get_running_app()
        session.root.current = 'work_order'

    def on_enter(self):
        session = PcpApp.get_running_app()
        request = call("object", "execute",
                       DB, session.uid, session.pwd,
                       "mrp.production",
                       "search_read",
                       [('state', 'not in', ['done', 'cancel', 'draft'])],
                       ["id", "name", "product_id", "product_qty", "date_planned_start", "state"])

        for index, production_order in enumerate(request):
            id = "{}".format(production_order.get("id"))
            order_item = ThreeLineIconListItem(
                id=id,
                text="Ordem de produção: {}".format(production_order.get("name")),
                secondary_text="Produto: {} \n Quantidade: {}".format(production_order.get("product_id")[1],
                                                                      int(production_order.get("product_qty"))),
                tertiary_text="Data Programada: {} \nSituação: {}".format(
                    production_order.get(
                        "date_planned_start"),
                    'Em Progresso' if production_order.get("state").__eq__('progress') else 'Confirmado'),
            )

            icon_button = IconLeftWidget(
                id=id,
                icon='view-list'
            )
            on_press_func = partial(self.change_to_os_screen, icon_button)

            icon_button.on_press = on_press_func
            order_item.add_widget(icon_button)

            self.ids.production_order_list.add_widget(order_item)


class WorkOrderScreen(MDScreen):
    pass


class CustomSnackbar(BaseSnackbar):
    text = StringProperty(None)
    icon = StringProperty(None)
    font_size = NumericProperty("15sp")


class WorkOrder(FloatLayout, HoverBehavior):

    def show(self):
        snackbar = CustomSnackbar(
            text="This is a snackbar!",
            icon="information",
            snackbar_x="10dp",
            snackbar_y="10dp",
            buttons=[MDFlatButton(text="ACTION", text_color=(1, 1, 1, 1))]
        )
        snackbar.size_hint_x = (
                                       Window.width - (snackbar.snackbar_x * 2)
                               ) / Window.width
        snackbar.open()

    def api_request(self, service_order_id, session, action):
        return requests.post(url="http://localhost:8069/workorder/{}".format(action),
                             data=json.dumps({
                                 "jsonrpc": "2.0",
                                 "params": {
                                     "id": int(service_order_id)  # ordem de serviço selecionada pelo usuário
                                 }
                             }).encode(),
                             cookies={
                                 "session_id": session.session_id
                             },
                             headers={"Content-Type": "application/json"})

    def update_process(self, button, action):
        session = PcpApp.get_running_app()
        service_order_id = button.parent.id

        snackbar = CustomSnackbar(
            icon="information",
            snackbar_x="10dp",
            snackbar_y="10dp",
            buttons=[MDFlatButton(text="Ok", text_color=(1, 1, 1, 1))]
        )
        snackbar.size_hint_x = (
                                       Window.width - (snackbar.snackbar_x * 2)
                               ) / Window.width

        try:
            request = self.api_request(service_order_id, session, action)
            if request.status_code.__eq__(200):
                workorder_id = json.loads(request.content.decode('utf-8')).get("result")[0]
                snackbar.text = "A operação de {} foi alterada para o status de {}".format(button.parent.text,
                                                                                           SERVICE_ORDER_STATE[
                                                                                               workorder_id.get(
                                                                                                   "state")])
                snackbar.open()
        except Exception:
            snackbar.text = "Erro crítico no sistema, relate ao administrador!"
            snackbar.open()

    def on_enter(self):

        def set_first_button(button):
            button.pos_hint = {"center_x": first_button_position.get("x"),
                               "center_y": first_button_position.get("y")}

        def set_second_button(button):
            button.pos_hint = {"center_x": second_button_position.get("x"),
                               "center_y": second_button_position.get("y")}

        first_button_position = {'x': 0.93, 'y': 0.50}
        second_button_position = {'x': 0.80, 'y': 0.50}
        session = PcpApp.get_running_app()
        work_production_screen = self.parent.manager.get_screen("work_production")

        request = call("object", "execute", DB, session.uid, session.pwd, "mrp.workorder", "search_read",
                       [('production_id', '=',
                         int(work_production_screen.children[0].children[0].ids.id_text_field.text))],
                       ["id", "name", "workcenter_id", "working_state", "date_planned_start",
                        "duration_expected", "duration", "state"])

        for index, service_order in enumerate(request):
            id = "{}".format(service_order.get("id"))
            service_order_item = ThreeLineListItem(
                id=id,
                text="{}".format(service_order.get("name")),
                secondary_text="Duração prevista: {} \n Duração Real: {}".format(
                    str(service_order.get("duration_expected")).replace('.', ':'),
                    str(service_order.get("duration")).replace('.', ':')),
                tertiary_text="Situação: {}".format(
                    SERVICE_ORDER_STATE[service_order.get("state")]),
            )

            """
                botão para iniciar a ordem de serviço.
            """
            start_button = MDRoundFlatButton(
                id="start_{}".format(id),
                text="Iniciar",
                text_color="white",
            )
            partial_start_button = partial(self.update_process, start_button, start_button.id.split("_")[0])
            start_button.on_press = partial_start_button

            """
                botão para pausar a ordem de serviço.
            """
            pause_button = MDRoundFlatButton(
                id="pause_{}".format(id),
                text="Pausar",
                text_color="white"
            )
            partial_pause_button = partial(self.pause_process, pause_button, pause_button.id.split("_")[0])
            pause_button.on_press = partial_pause_button

            """
                botão para finalizar a ordem de serviço.
            """
            finish_button = MDRoundFlatButton(
                id="finish_{}".format(id),
                text="Finalizar",
                text_color="white"
            )
            partial_finish_button = partial(self.finish_process, finish_button, finish_button.id.split("_")[0])
            finish_button.on_press = partial_finish_button

            """
                em razão da Situação da ordem de serviço, disponibilizar apenas o botões permitidos.
            """
            if service_order.get("state").__eq__("pending"):
                set_first_button(start_button)
                service_order_item.add_widget(start_button)
            elif service_order.get("state").__eq__("progress"):
                set_first_button(pause_button)
                set_second_button(finish_button)
                service_order_item.add_widget(pause_button)
                service_order_item.add_widget(finish_button)
            elif service_order.get("state").__eq__("ready"):
                set_first_button(start_button)
                service_order_item.add_widget(start_button)

            self.ids.service_order_list.add_widget(service_order_item)


class WindowManager(ScreenManager):
    pass


class PcpApp(MDApp):
    uid = ''
    session_id = ''
    pwd = ''

    def build(self):
        self.theme_cls.primary_palette = 'Purple'
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_hue = "700"

        return Builder.load_file('core/views/pcp.kv')


PcpApp().run()
