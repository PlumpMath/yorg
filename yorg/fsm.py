from sys import exit
from yyagl.gameobject import Fsm
from yyagl.racing.season.season import SingleRaceSeason
from yyagl.engine.network.server import Server
from yyagl.engine.network.client import Client
from yyagl.engine.log import LogMgr
from menu.menu import YorgMenu, MenuProps
from menu.exitmenu.menu import ExitMenu
from .utils import Utils


class YorgFsm(Fsm):

    def __init__(self, mdt):
        Fsm.__init__(self, mdt)
        self.defaultTransitions = {
            'Menu': ['Race', 'Exit'],
            'Race': ['Ranking', 'Menu', 'Exit'],
            'Ranking': ['Tuning', 'Exit'],
            'Tuning': ['Menu', 'Race', 'Exit'],
            'Exit': ['Exit']}
        self.load_txt = None
        self.preview = None
        self.cam_tsk = None
        self.cam_node = None
        self.ranking_texts = None
        self.send_tsk = None
        self.cam_pivot = None
        self.ready_clients = None
        self.curr_load_txt = None
        self.__menu = None
        self.race = None
        self.__exit_menu = None

    def enterMenu(self):
        LogMgr().log('entering Menu state')
        menu_props = MenuProps(
            Utils().menu_args, self.mdt.options,
            ['kronos', 'themis', 'diones', 'iapeto', 'phoibe', 'rea'],
            'assets/images/cars/%s.png',
            eng.curr_path + 'assets/models/cars/%s/phys.yml',
            ['desert', 'mountain'], [_('desert'), _('mountain')],
            'assets/images/tracks/%s.png',
            self.mdt.options['settings']['player_name'],
            ['assets/images/drivers/driver%s.png',
             'assets/images/drivers/driver%s_sel.png'],
            'assets/images/cars/%s_sel.png',
            self.mdt.options['development']['multiplayer'],
            'assets/images/gui/yorg_title.png',
            'http://feeds.feedburner.com/ya2tech?format=xml',
            'http://www.ya2.it', 'save' in self.mdt.options.dct,
            self.mdt.options['development']['season'], ['prototype', 'desert'],
            'http://www.ya2.it/support-us', Utils().drivers)
        self.__menu = YorgMenu(menu_props)
        self.__menu.gui.menu.attach_obs(self.mdt.logic.on_input_back)
        self.__menu.gui.menu.attach_obs(self.mdt.logic.on_options_back)
        self.__menu.gui.menu.attach_obs(self.mdt.logic.on_car_selected)
        self.__menu.gui.menu.attach_obs(self.mdt.logic.on_car_selected_season)
        self.__menu.gui.menu.attach_obs(self.mdt.logic.on_driver_selected)
        self.__menu.gui.menu.attach_obs(self.mdt.logic.on_exit)
        self.__menu.gui.menu.attach_obs(self.mdt.logic.on_continue)
        self.mdt.logic.menu_start()
        if self.mdt.logic.season:
            self.mdt.logic.season.detach_obs(self.mdt.event.on_season_end)
            self.mdt.logic.season.detach_obs(self.mdt.event.on_season_cont)

    def exitMenu(self):
        LogMgr().log('exiting Menu state')
        self.__menu.destroy()
        self.mdt.audio.menu_music.stop()

    def enterRace(self, track_path='', car_path='', drivers=''):
        LogMgr().log('entering Race state')
        base.ignore('escape-up')
        if 'save' not in self.mdt.options.dct:
            self.mdt.options['save'] = {}
        self.mdt.options['save']['track'] = track_path
        self.mdt.options['save']['car'] = car_path
        self.mdt.options['save']['drivers'] = drivers
        self.mdt.options.store()
        keys = self.mdt.options['settings']['keys']
        joystick = self.mdt.options['settings']['joystick']
        sounds = {
            'engine': 'assets/sfx/engine.ogg',
            'brake': 'assets/sfx/brake.ogg',
            'crash': 'assets/sfx/crash.ogg',
            'crash_hs': 'assets/sfx/crash_high_speed.ogg',
            'lap': 'assets/sfx/lap.ogg',
            'landing': 'assets/sfx/landing.ogg'}
        if Server().is_active:
            self.season.create_race_server(keys, joystick, sounds)
        elif Client().is_active:
            self.season.create_race_client(keys, joystick, sounds)
        else:
            race_props = self.mdt.logic.build_race_props(
                car_path, drivers, track_path, keys, joystick, sounds)
            self.mdt.logic.season.create_race(race_props)
        LogMgr().log('selected drivers: ' + str(drivers))
        self.mdt.logic.season.race.logic.drivers = drivers
        track_name_transl = track_path
        track_dct = {'desert': _('desert'), 'mountain': _('mountain')}
        if track_path in track_dct:
            track_name_transl = track_dct[track_path]
        singlerace = game.logic.season.__class__ == SingleRaceSeason
        self.mdt.logic.season.race.fsm.demand(
            'Loading', track_path, car_path, [], drivers,
            ['prototype', 'desert'], track_name_transl, singlerace,
            ['kronos', 'themis', 'diones', 'iapeto', 'phoibe', 'rea'],
            'assets/images/cars/%s_sel.png',
            'assets/images/drivers/driver%s_sel.png',
            game.options['settings']['joystick'],
            game.options['settings']['keys'], Utils().menu_args,
            'assets/sfx/countdown.ogg')
        self.mdt.logic.season.race.attach_obs(self.mdt.logic.on_race_loaded)
        exit_meth = self.mdt.logic.on_ingame_exit_confirm
        self.mdt.logic.season.race.attach_obs(exit_meth)

    def exitRace(self):
        LogMgr().log('exiting Race state')
        self.mdt.logic.season.race.destroy()
        base.accept('escape-up', self.demand, ['Exit'])

    def enterRanking(self):
        self.mdt.logic.season.ranking.show()
        eng.do_later(10, self.demand, ['Tuning'])

    def exitRanking(self):
        self.mdt.logic.season.ranking.hide()

    def enterTuning(self):
        self.mdt.logic.season.tuning.show_gui()

    def exitTuning(self):
        self.mdt.logic.season.tuning.hide_gui()

    def enterExit(self):
        if not self.mdt.options['development']['show_exit']:
            exit()
        self.__exit_menu = ExitMenu(Utils().menu_args)

    def exitExit(self):
        self.__exit_menu.destroy()
