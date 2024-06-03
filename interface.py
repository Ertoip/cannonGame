from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.app import App
from kivy.lang import Builder


class OpenWindow(BoxLayout):
    pass

class MenuWindow(BoxLayout):
    pass

class HelpWindow(BoxLayout):
    pass

class SaveWindow(BoxLayout):
    pass

class HallWindow(BoxLayout):
    pass

class OpenScreen(Screen):
    pass

class MenuScreen(Screen):
    pass

class HelpScreen(Screen):
    pass

class SaveScreen(Screen):
    pass

class HallScreen(Screen):
    pass

class InterfaceApp(App):
    def build(self):
        Builder.load_file('open.kv')
        Builder.load_file('menu.kv')
        Builder.load_file('help.kv')
        Builder.load_file('save.kv')
        Builder.load_file('hall.kv')
        self.sm = ScreenManager()
        self.sm.add_widget(OpenScreen(name='open'))
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(HelpScreen(name='help'))
        self.sm.add_widget(SaveScreen(name='save'))
        self.sm.add_widget(HallScreen(name='hall'))
        # self.sm.add_widget(CannonApp(name='game'))
        return self.sm
    
    def switch_to_menu(self):
        self.sm.current = 'menu'

    def switch_to_help(self):
        self.sm.current = 'help'

    def switch_to_save(self):
        self.sm.current = 'save'

    def switch_to_hall(self):
        self.sm.current = 'hall'

    # def start_new_game(self):
    #    self.sm.current = 'game'
    
    def close_app(self):
        self.stop()

sample_app = InterfaceApp()
sample_app.run()