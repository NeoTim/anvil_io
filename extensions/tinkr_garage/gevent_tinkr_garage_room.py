from core.core_gevent.room_server_base import *
import random


"""
    client game events
"""


@app_client_game_event
class EventClientJoinGame(ClientGameEvent):
    event_id = '\x00'
    var_struct = [
        ('car_id', 'i'),
        ('room_id', 'i')
    ]


@app_client_game_event
class EventClientExitGame(ClientGameEvent):
    event_id = '\x01'
    var_struct = []


@app_client_game_event
class EventClientFire(ClientGameEvent):
    event_id = '\x02'
    var_struct = [
        ('weapon_id', 'i')
    ]


@app_client_game_event
class EventClientHit(ClientGameEvent):
    event_id = '\x03'
    var_struct = [
        ('damage', 'i'),
        ('hit_pos', 'iii'),
        ('hit_cid', 'i')
    ]


@app_client_game_event
class EventClientPickUpWeapon(ClientGameEvent):
    event_id = '\x04'
    var_struct = [
        ('weapon_id', 'i'),
        ('weapon_type', 'i'),
        ('equip_slot', 'i')
    ]


@app_client_game_event
class EventClientDropWeapon(ClientGameEvent):
    event_id = '\x05'
    var_struct = [
        ('weapon_id', 'i'),
        ('weapon_type', 'i'),
        ('drop_pos', 'iii')
    ]


@app_client_game_event
class EventClientPing(ClientGameEvent):
    event_id = '\x06'
    var_struct = []


@app_client_game_event
class EventClientLogin(ClientGameEvent):
    event_id = '\x07'
    var_struct = [
        ('car_id', 'i'),
        ('session', 'i')
    ]


@app_client_game_event
class EventClientLogout(ClientGameEvent):
    event_id = '\x08'
    var_struct = []


@app_client_game_event
class EventClientHeal(ClientGameEvent):
    event_id = '\x09'
    var_struct = [
        ('heal_val', 'i')
    ]


@app_client_game_event
class EventClientEquipWeapon(ClientGameEvent):
    event_id = '\x0a'
    var_struct = [
        ('weapon_id', 'i'),
        ('weapon_type', 'i')
    ]


@app_client_game_event
class EventClientRelogin(ClientGameEvent):
    event_id = '\x0b'
    var_struct = [
        ('session', 'i')
    ]


@app_client_game_event
class EventClientStartGame(ClientGameEvent):
    event_id = '\x0c'
    var_struct = [
        ('car_id', 'i'),
        ('grid_x', 'c'),
        ('grid_y', 'c'),
        ('pos_x', 'c'),
        ('pos_y', 'c'),
        ('pos_z', 'h'),
        ('rot', 'ccc')
    ]


"""
    server game events
"""


@app_server_game_event
class EventServerSpawnPlayer(ServerGameEvent):
    event_id = '\x00'
    var_struct = [
        ('car_id', 'i'),
        ('grid_x', 'c'),
        ('grid_y', 'c'),
        ('pos_x', 'c'),
        ('pos_y', 'c'),
        ('pos_z', 'h'),
        ('rot', 'ccc'),
        ('has_ship', 'c')
    ]


@app_server_game_event
class EventServerLogout(ServerGameEvent):
    event_id = '\x01'
    var_struct = []


@app_server_game_event
class EventServerFire(ServerGameEvent):
    event_id = '\x02'
    var_struct = [
        ('weapon_id', 'i')
    ]


@app_server_game_event
class EventServerDamage(ServerGameEvent):
    event_id = '\x03'
    var_struct = [
        ('fire_cid', 'i'),
        ('damage', 'i')
    ]


@app_server_game_event
class EventServerStartGame(ServerGameEvent):
    event_id = '\x04'
    var_struct = []


@app_server_game_event
class EventServerSpawnGameObject(ServerGameEvent):
    event_id = '\x05'
    var_struct = [
        ('object_id', 'i'),
        ('object_type', 'i'),
        ('object_subtype', 'i'),
        ('pos_index', 'i')
    ]


@app_server_game_event
class EventServerDestroyWeapon(ServerGameEvent):
    event_id = '\x06'
    var_struct = [
        ('weapon_id', 'i')
    ]


@app_server_game_event
class EventServerEquipWeapon(ServerGameEvent):
    event_id = '\x07'
    var_struct = [
        ('weapon_id', 'i'),
        ('weapon_type', 'i'),
        ('equip_slot', 'i')
    ]


@app_server_game_event
class EventServerEchoPing(ServerGameEvent):
    event_id = '\x08'
    var_struct = [
        ('ping_start_stamp', 'i')
    ]


@app_server_game_event
class EventServerUpdateSandStorm(ServerGameEvent):
    event_id = '\x09'
    var_struct = [
        ('cur_center', 'cccc'),    # grid_x, grid_y, sub_grid_x, sub_grid_y, 1 byte for each
        ('cur_radius', 'i'),
        ('shrink_speed', 'i'),  # unit per sec
        ('time_to_appear_next', 'h'),  # duration of current storm (seconds)
        ('time_to_shrink', 'h')  # time before the shrink (seconds)
    ]


@app_server_game_event
class EventServerPlayerDeath(ServerGameEvent):
    event_id = '\x0b'
    var_struct = [
        ('killed_cid', 'i'),
        ('killer_id', 'i')
    ]


@app_server_game_event
class EventServerPickUpWeapon(ServerGameEvent):
    event_id = '\x0c'
    var_struct = [
        ('weapon_id', 'i'),
        ('weapon_type', 'i')
    ]


@app_server_game_event
class EventServerReloginResult(ServerGameEvent):
    event_id = '\x0d'
    var_struct = [
        ('res', 'c')
    ]


@app_server_game_event
class EventServerMatchGameResult(ServerGameEvent):
    event_id = '\x0e'
    var_struct = [
        ('res', 'c')
    ]


class TinkrGarageRoom(RoomServerBase):

    AI_UPDATE_RATE = 0.3

    class ClientState:
        def __init__(self):
            self.grid_x = '\x15'
            self.grid_y = '\x33'
            self.pos = ['\xa0', '\xa0', 2200]
            self.rot = ['\x00', '\x00', '\x00']
            self.vid = 3
            self.HP = 100
            self.spawn_slot = 0
            self.is_faked = False   # if a client is AI
            self.last_state_stamp = 0   # time stamp of last state update (in client's system time)
            self.is_dead = False

    class GameModel:

        """
        the model of the game
        """

        MAP_X_W = 204000.0
        MAP_Y_W = 204000.0
        GRID_NUM = 256
        SUB_GRID_NUM = 256
        GRID_WIDTH = MAP_X_W / GRID_NUM
        SUB_GRID_WIDTH = MAP_X_W / (GRID_NUM * SUB_GRID_NUM)

        class GameState:

            WAITING_CLIENTS = 0
            GAME_RUNNING = 1

        class Weapon:
            def __init__(self, weapon_id, weapon_type):
                self.weapon_id = weapon_id
                self.weapon_type = weapon_type

        def __init__(self):

            self.game_state = self.GameState.WAITING_CLIENTS

            self.cur_storm_center = [0, 0]
            self.cur_storm_radius = 150000
            self.cur_storm_duration = 15  # secs
            self.last_storm_update_stamp = 0  # last stamp of storm update
            self.storm_shrink_start_stamp = -1  # stamp <= 0 means not shrinking
            self.storm_shrink_delay = 5  # secs, count down before shrink happened
            self.storm_shrink_duration = 5  # secs, define the shrink speed

            self.storm_pkg_count = 0

            self.prev_storm_center = [0, 0]
            self.prev_storm_radius = 150000
            self.next_storm_center = [0, 0]
            self.next_storm_radius = 150000

            self.last_storm_damage_stamp = time.time()      # damage calc timer stamp

            self.ENABLE_STORM = True    # flag of storm enabling

            # init weapons
            # weapon_id => weapon
            self.weapons = {}
            for i in range(15):
                if i == 4:
                    self.weapons[i + 1] = self.Weapon(i + 1, 2)
                elif i == 13:
                    self.weapons[i + 1] = self.Weapon(i + 1, 3)
                elif i == 14:
                    self.weapons[i + 1] = self.Weapon(i + 1, 4)
                else:
                    self.weapons[i + 1] = self.Weapon(i + 1, 1)

        def true_xy_to_grid(self, true_x, true_y):
            """ true x, y to (grid x, grid y, sub grid x, sub grid y) """
            x_abs = true_x + self.MAP_X_W * 0.5
            y_abs = true_y + self.MAP_Y_W * 0.5
            grid_x = int(x_abs / self.GRID_WIDTH)
            grid_y = int(y_abs / self.GRID_WIDTH)
            sub_grid_x = int((x_abs - grid_x * self.GRID_WIDTH) / self.SUB_GRID_WIDTH)
            sub_grid_y = int((y_abs - grid_y * self.GRID_WIDTH) / self.SUB_GRID_WIDTH)
            return [grid_x, grid_y, sub_grid_x, sub_grid_y]

        def grid_xy_to_true(self, grid_x, grid_y, sub_grid_x, sub_grid_y):
            true_x = grid_x * self.GRID_WIDTH + sub_grid_x * self.SUB_GRID_WIDTH - self.MAP_X_W * 0.5
            true_y = grid_y * self.GRID_WIDTH + sub_grid_y * self.SUB_GRID_WIDTH - self.MAP_Y_W * 0.5
            return [true_x, true_y]

        def game_model_init(self):

            self.game_state = self.GameState.WAITING_CLIENTS

            self.cur_storm_center = [0, 0]
            self.cur_storm_radius = 150000
            self.cur_storm_duration = 15  # secs
            self.last_storm_update_stamp = 0  # last stamp of storm update
            self.storm_shrink_start_stamp = -1  # stamp <= 0 means not shrinking
            self.storm_shrink_delay = 5  # secs, count down before shrink happened
            self.storm_shrink_duration = 5  # secs, define the shrink speed

            self.storm_pkg_count = 0

            self.prev_storm_center = [0, 0]
            self.prev_storm_radius = 150000
            self.next_storm_center = [0, 0]
            self.next_storm_radius = 150000

            self.last_storm_damage_stamp = time.time()

            # init weapons
            # TODO: better reset weapons
            self.weapons = {}
            for i in range(15):
                if i == 4:
                    self.weapons[i + 1] = self.Weapon(i + 1, 2)
                elif i == 13:
                    self.weapons[i + 1] = self.Weapon(i + 1, 3)
                elif i == 14:
                    self.weapons[i + 1] = self.Weapon(i + 1, 4)
                else:
                    self.weapons[i + 1] = self.Weapon(i + 1, 1)

    def __init__(self, gate_server_ref, room_id, server_name='tinkr_room'):
        RoomServerBase.__init__(self, gate_server_ref, room_id, server_name)
        self.game_model = self.GameModel()
        self.start_stamp = time.time()  # the timestamp of starting time
        self.match_str = ''     # string used to match particular room. each room has a unique string
        self.last_ai_update_stamp = 0

    def pack_client_state(self, cid):
        state = self.client_infos[cid].state
        return pack('<cccchccc', state.grid_x, state.grid_y, state.pos[0], state.pos[1], state.pos[2], state.rot[0], state.rot[1], state.rot[2])

    def unpack_client_state(self, pkg_data):
        """
        NOTE: not specified parameters will be overwritten with default values
        :param pkg_data:
        :return:
        """
        state = self.ClientState()
        seq = unpack('<i', pkg_data[1:5])[0]
        state_data = pkg_data[9:]
        (grid_x, grid_y, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<cccchccc', state_data)
        state.grid_x = grid_x
        state.grid_y = grid_y
        state.pos[0] = pos_x
        state.pos[1] = pos_y
        state.pos[2] = pos_z
        state.rot[0] = rot_x
        state.rot[1] = rot_y
        state.rot[2] = rot_z
        state.last_state_stamp = seq
        return state

    def update_client_state(self, cid, new_state):
        if cid in self.client_infos:
            if self.client_infos[cid].state.HP <= 0:
                # print 'client', cid, 'dead. no need to sync'
                return False    # no need to update dead client
            if new_state.last_state_stamp > self.client_infos[cid].state.last_state_stamp:
                self.client_infos[cid].state.grid_x = new_state.grid_x
                self.client_infos[cid].state.grid_y = new_state.grid_y
                self.client_infos[cid].state.pos = new_state.pos
                self.client_infos[cid].state.rot = new_state.rot
                self.client_infos[cid].state.last_state_stamp = new_state.last_state_stamp
                return True
            else:
                print 'old state:', new_state.last_state_stamp, ', not update'
                return False
        return False

    def post_add_client(self, cid):
        if len(self.client_infos) == 1:
            # print 'game start'
            # self.game_model.game_state = self.GameModel.GameState.GAME_RUNNING
            # self.start_stamp = time.time()
            pass

    def clear_room(self):
        print 'clear room'
        self.game_model.game_model_init()

    def post_remove_client(self, cid):
        if len(self.client_infos) == 0:
            print 'all clients leaved.'
            self.clear_room()   # TESTING

    def tick_client_state_sync(self):
        CLIENT_UPDATE_INTERVAL = 1.0 / self.CLIENT_UPDATE_RATE
        while True:
            try:
                data_dict_to_send = {}  # cid => [data to send to this cid, data count]
                for target_cid in self.client_infos:
                    grid_x_target_cid = unpack('<h', self.client_infos[target_cid].state.grid_x + '\x00')[0]
                    grid_y_target_cid = unpack('<h', self.client_infos[target_cid].state.grid_y + '\x00')[0]
                    data_target_cid = pack('<i', target_cid) + self.pack_client_state(target_cid)
                    for cid in self.client_infos:
                        if cid <= target_cid or not self.client_infos[cid].need_update:
                            continue
                        # optimization for package size
                        grid_x_cid = unpack('<h', self.client_infos[cid].state.grid_x + '\x00')[0]
                        grid_y_cid = unpack('<h', self.client_infos[cid].state.grid_y + '\x00')[0]
                        # if too far, don't send
                        if abs(grid_x_target_cid - grid_x_cid) > 60 or abs(grid_y_target_cid - grid_y_cid) > 60:
                            continue
                        data_cid = pack('<i', cid) + self.pack_client_state(cid)
                        if target_cid not in data_dict_to_send:  # if not ever recorded
                            data_dict_to_send[target_cid] = [data_cid, 1]
                            data_dict_to_send[cid] = [data_target_cid, 1]
                        else:
                            data_dict_to_send[target_cid][0] += data_cid
                            data_dict_to_send[target_cid][1] += 1
                            data_dict_to_send[cid][0] += data_target_cid
                            data_dict_to_send[cid][1] += 1
                # send state data to clients
                for target_cid in data_dict_to_send:
                    data_sent = pack('<i', data_dict_to_send[target_cid][1]) + data_dict_to_send[target_cid][0]
                    self.gate_server_ref.send_package([target_cid], data_sent, '\x11')
            except Exception, e:
                print e
                print 'sync states error'
            gevent.sleep(CLIENT_UPDATE_INTERVAL)

    @on_client_game_event(EventClientJoinGame)
    def on_client_join_game(self, evt):

        # TESTING
        self.start_stamp = time.time()
        self.game_model.game_state = self.GameModel.GameState.GAME_RUNNING

        # join game event
        vid = evt.var['car_id']
        print 'vehicle id', vid
        token = 0
        login_success = False
        cid = evt.from_cid
        if cid in self.client_infos:
            login_success = True
        else:
            print 'client', cid, 'not in room', self.room_id
        if login_success:

            # init to-join client info
            self.client_infos[cid].state.vid = vid

            # echo match game event
            evt_match_game = EventServerMatchGameResult()
            evt_match_game.from_cid = -1
            evt_match_game.var['res'] = '\x01'
            self.game_event_manager.send_server_event(cid, evt_match_game)

    @on_client_game_event(EventClientStartGame)
    def on_client_start_game(self, evt):
        # echo start game
        # update client initial info
        cid = evt.from_cid
        if cid not in self.client_infos:
            print 'game start failed. client', cid, 'not in room', self.room_id
            return
        self.client_infos[cid].state.grid_x = evt.var['grid_x']
        self.client_infos[cid].state.grid_y = evt.var['grid_y']
        self.client_infos[cid].state.pos[0] = evt.var['pos_x']
        self.client_infos[cid].state.pos[1] = evt.var['pos_y']
        self.client_infos[cid].state.pos[2] = evt.var['pos_z']
        self.client_infos[cid].state.rot[0] = evt.var['rot'][0]
        self.client_infos[cid].state.rot[1] = evt.var['rot'][1]
        self.client_infos[cid].state.rot[2] = evt.var['rot'][2]

        # notify new client of existing clients
        evt_spawn_old = EventServerSpawnPlayer()
        for existing_cid in self.client_infos:
            if existing_cid != cid:
                evt_spawn_old.from_cid = existing_cid
                existing_client_state = self.client_infos[existing_cid].state
                evt_spawn_old.var['car_id'] = existing_client_state.vid
                evt_spawn_old.var['grid_x'] = existing_client_state.grid_x
                evt_spawn_old.var['grid_y'] = existing_client_state.grid_y
                evt_spawn_old.var['pos_x'] = existing_client_state.pos[0]
                evt_spawn_old.var['pos_y'] = existing_client_state.pos[1]
                evt_spawn_old.var['pos_z'] = existing_client_state.pos[2]
                evt_spawn_old.var['rot'] = existing_client_state.rot
                evt_spawn_old.var['has_ship'] = '\x00'  # False
                self.game_event_manager.send_server_event(cid, evt_spawn_old)

        # notify all clients to add new client
        evt_spawn_new = EventServerSpawnPlayer()
        evt_spawn_new.from_cid = cid
        current_state = self.client_infos[cid].state
        evt_spawn_new.var['car_id'] = current_state.vid
        evt_spawn_new.var['grid_x'] = current_state.grid_x
        evt_spawn_new.var['grid_y'] = current_state.grid_y
        evt_spawn_new.var['pos_x'] = current_state.pos[0]
        evt_spawn_new.var['pos_y'] = current_state.pos[1]
        evt_spawn_new.var['pos_z'] = current_state.pos[2]
        evt_spawn_new.var['rot'] = current_state.rot
        evt_spawn_new.var['has_ship'] = '\x01'  # True
        # broadcast event
        self.game_event_manager.broadcast_server_event(evt_spawn_new, [])

        # start game
        evt_start_game = EventServerStartGame()
        evt_start_game.from_cid = -1
        self.game_event_manager.send_server_event(cid, evt_start_game)
        pass

    @on_client_game_event(EventClientExitGame)
    def on_client_exit_game(self, evt):
        self.gate_server_ref.run_command(
            'quit_room',
            evt.from_cid
        )
        pass

    @on_client_game_event(EventClientFire)
    def on_client_fire(self, evt):
        # fire event
        """
            | header | weapon_id |
                10         4
        """
        print 'fire event'
        weapon_id = evt.var['weapon_id']
        # broadcast_data(data_sent, sock_server, clients, [cid])
        evt_fire = EventServerFire()
        evt_fire.from_cid = evt.from_cid
        evt_fire.var['weapon_id'] = weapon_id
        self.game_event_manager.broadcast_server_event(evt_fire, [evt.from_cid])

    @on_client_game_event(EventClientHit)
    def on_client_hit(self, evt):
        # hit event
        """
            | header | damage | hit_pos | hit_cid |
                10        4       4x3        4
        """
        print 'hit event'
        fire_cid = evt.from_cid
        hit_cid = evt.var['hit_cid']
        init_damage = evt.var['damage']
        damage = float(init_damage) / 10000
        self.client_infos[hit_cid].state.HP -= damage
        print 'client', fire_cid, 'hit', hit_cid, ', damage', damage
        evt_damage = EventServerDamage()
        evt_damage.from_cid = hit_cid
        evt_damage.var['fire_cid'] = fire_cid
        evt_damage.var['damage'] = init_damage
        self.game_event_manager.broadcast_server_event(evt_damage)

        # determine death
        # TODO: centralize death event
        if not self.client_infos[hit_cid].state.is_dead and self.client_infos[hit_cid].state.HP <= 0:
            self.client_infos[hit_cid].state.is_dead = True
            print 'client', hit_cid, 'dead'
            evt_death = EventServerPlayerDeath()
            evt_death.from_cid = hit_cid
            evt_death.var['killed_cid'] = hit_cid
            evt_death.var['killer_id'] = fire_cid
            self.game_event_manager.broadcast_server_event(evt_death)

    @on_client_game_event(EventClientPickUpWeapon)
    def on_client_pick_up_weapon(self, evt):
        # pick up weapon event
        print 'pick up weapon event'
        weapon_id = evt.var['weapon_id']
        weapon_type = evt.var['weapon_type']
        equip_slot = evt.var['equip_slot']

        # TODO: add real check
        pick_success = True
        if weapon_id not in self.game_model.weapons:
            print 'wid', weapon_id, 'wtype', weapon_type
            print 'pick up weapon failed'
            pick_success = False

        if pick_success:

            # destroy weapon event
            evt_destroy_weapon = EventServerDestroyWeapon()
            evt_destroy_weapon.from_cid = evt.from_cid
            evt_destroy_weapon.var['weapon_id'] = weapon_id
            self.game_event_manager.broadcast_server_event(evt_destroy_weapon)

            # pick up weapon event
            evt_pick_up_weapon = EventServerPickUpWeapon()
            evt_pick_up_weapon.from_cid = evt.from_cid
            evt_pick_up_weapon.var['weapon_id'] = weapon_id
            evt_pick_up_weapon.var['weapon_type'] = weapon_type
            self.game_event_manager.send_server_event(evt.from_cid, evt_pick_up_weapon)

            # remove weapon
            self.game_model.weapons.pop(weapon_id)

            # equip weapon event
            # evt_equip_weapon = EventServerEquipWeapon()
            # evt_equip_weapon.from_cid = evt.from_cid
            # evt_equip_weapon.var['weapon_id'] = weapon_id
            # evt_equip_weapon.var['weapon_type'] = weapon_type
            # evt_equip_weapon.var['equip_slot'] = equip_slot
            # self.game_event_manager.broadcast_server_event(evt_equip_weapon)

    @on_client_game_event(EventClientEquipWeapon)
    def on_client_equip_weapon(self, evt):
        print 'equip weapon event'
        evt_equip_weapon = EventServerEquipWeapon()
        evt_equip_weapon.from_cid = evt.from_cid
        print 'wid', evt.var['weapon_id']
        print 'wtype', evt.var['weapon_type']
        evt_equip_weapon.var['weapon_id'] = evt.var['weapon_id']
        evt_equip_weapon.var['weapon_type'] = evt.var['weapon_type']
        evt_equip_weapon.var['equip_slot'] = 1  # may need later
        self.game_event_manager.broadcast_server_event(evt_equip_weapon, [evt.from_cid])

    @on_client_game_event(EventClientPing)
    def on_client_ping(self, evt):
        echo_evt = EventServerEchoPing()
        echo_evt.from_cid = evt.from_cid
        echo_evt.var['ping_start_stamp'] = evt.time_stamp
        self.game_event_manager.send_server_event(evt.from_cid, echo_evt)

    @on_client_game_event(EventClientHeal)
    def on_client_heal(self, evt):
        from_cid = evt.from_cid
        if from_cid in self.client_infos:
            hp = self.client_infos[from_cid].state.HP
            hp += evt.var['heal_val']
            if hp > 100:
                hp = 100
            print 'client', from_cid, 'healed to', hp
            self.client_infos[from_cid].state.HP = hp

    def tick_extra(self):
        """
        coroutine = main game model logic
        """
        GAME_LOGIC_INTERVAL = 1.0 / 60
        while True:
            try:
                if self.game_model.game_state == self.GameModel.GameState.GAME_RUNNING:
                    # update fake clients
                    if time.time() - self.last_ai_update_stamp > 1.0 / self.AI_UPDATE_RATE:
                        self.last_ai_update_stamp = time.time()
                        for ai_ind in range(100):
                            if ai_ind in self.client_infos:
                                self.client_infos[ai_ind].state.grid_x = pack('<i', random.randint(0, 5))[0]
                                self.client_infos[ai_ind].state.grid_y = pack('<i', random.randint(0, 5))[0]
                                self.client_infos[ai_ind].need_update = True
                                pass
                    # storm logic
                    if self.game_model.ENABLE_STORM:
                        # calculate shrinking storm
                        if self.game_model.storm_shrink_start_stamp > 0:
                            shrink_time = time.time() - self.game_model.storm_shrink_start_stamp    # time after shrink start
                            if shrink_time > 0:
                                if shrink_time > self.game_model.storm_shrink_duration:
                                    self.game_model.cur_storm_center[0] = self.game_model.next_storm_center[0]
                                    self.game_model.cur_storm_center[1] = self.game_model.next_storm_center[1]
                                    self.game_model.cur_storm_radius = self.game_model.next_storm_radius
                                    self.game_model.storm_shrink_start_stamp = -1
                                    print 'shrinking done. current radius', self.game_model.cur_storm_radius, 'current center', self.game_model.cur_storm_center[0], self.game_model.cur_storm_center[1]
                                else:
                                    alpha = shrink_time / self.game_model.storm_shrink_duration
                                    self.game_model.cur_storm_center[0] = (1 - alpha) * self.game_model.prev_storm_center[0] + alpha * self.game_model.next_storm_center[0]
                                    self.game_model.cur_storm_center[1] = (1 - alpha) * self.game_model.prev_storm_center[1] + alpha * self.game_model.next_storm_center[1]
                                    self.game_model.cur_storm_radius = (1 - alpha) * self.game_model.prev_storm_radius + alpha * self.game_model.next_storm_radius
                        # calculate storm damage
                        # TESTING
                        if time.time() - self.game_model.last_storm_damage_stamp > 2:   # tick every 2 secs
                            self.game_model.last_storm_damage_stamp = time.time()
                            # SHOULD BE cur_storm_center
                            # cur_center_xy = self.game_model.grid_xy_to_true(21, 51, 160, 160)
                            cur_center_xy = self.game_model.cur_storm_center
                            # print 'damage calc center:', self.game_model.cur_storm_center, ', damage radius:', self.game_model.cur_storm_radius
                            # print 'current storm center', cur_center_xy
                            for cid in self.client_infos:
                                if self.client_infos[cid].state.HP > 0:
                                    # print 'client', cid, 'HP', self.client_infos[cid].state.HP
                                    client_xy = self.game_model.grid_xy_to_true(
                                        unpack('<h', self.client_infos[cid].state.grid_x + '\x00')[0],
                                        unpack('<h', self.client_infos[cid].state.grid_y + '\x00')[0],
                                        unpack('<h', self.client_infos[cid].state.pos[0] + '\x00')[0],
                                        unpack('<h', self.client_infos[cid].state.pos[1] + '\x00')[0]
                                    )
                                    # print 'client pos', client_xy
                                    dx = client_xy[0] - cur_center_xy[0]
                                    dy = client_xy[1] - cur_center_xy[1]
                                    if dx * dx + dy * dy > self.game_model.cur_storm_radius * self.game_model.cur_storm_radius:
                                        damage = 10000
                                        # print 'storm damage', damage
                                        self.client_infos[cid].state.HP -= damage / 10000
                                        evt_damage = EventServerDamage()
                                        evt_damage.from_cid = cid   # damaged client
                                        evt_damage.var['fire_cid'] = -1  # server
                                        evt_damage.var['damage'] = damage
                                        self.game_event_manager.broadcast_server_event(evt_damage)

                                        # determine death
                                        # TODO: centralize death event
                                        if not self.client_infos[cid].state.is_dead and self.client_infos[cid].state.HP <= 0:
                                            self.client_infos[cid].state.is_dead = True
                                            print 'client', cid, 'dead'
                                            evt_death = EventServerPlayerDeath()
                                            evt_death.from_cid = cid
                                            evt_death.var['killed_cid'] = cid
                                            evt_death.var['killer_id'] = -1  # -1 == storm
                                            self.game_event_manager.broadcast_server_event(evt_death)
                        # update sand storm
                        storm_span = self.game_model.cur_storm_duration
                        if self.game_model.storm_pkg_count > 1:   # if not first update, accumulate shrink delay and shrink time
                            storm_span = self.game_model.cur_storm_duration + self.game_model.storm_shrink_delay + self.game_model.storm_shrink_duration
                        if time.time() - self.game_model.last_storm_update_stamp > storm_span:
                            # if time.time() - self.start_stamp < 15:  # TESTING
                            #     return
                            # counter update
                            self.game_model.storm_pkg_count += 1
                            print 'storm update at time', time.time()
                            self.game_model.last_storm_update_stamp = time.time()
                            # calculate next storm
                            # self.game_model.cur_storm_radius = self.game_model.next_storm_radius
                            if self.game_model.storm_pkg_count > 1:
                                self.game_model.next_storm_radius -= 5000
                                while self.game_model.next_storm_radius <= 0:
                                    self.game_model.next_storm_radius += 5000
                                self.game_model.next_storm_center[0] = self.game_model.cur_storm_center[0] + random.randint(1, 20000) - 10000
                                self.game_model.next_storm_center[1] = self.game_model.cur_storm_center[1] + random.randint(1, 20000) - 10000
                            # self.game_model.cur_storm_duration = 15
                            # must update last storm info
                            for i in range(len(self.game_model.cur_storm_center)):
                                self.game_model.prev_storm_center[i] = self.game_model.cur_storm_center[i]
                            self.game_model.prev_storm_radius = self.game_model.cur_storm_radius
                            # send update event
                            evt_storm_update = EventServerUpdateSandStorm()
                            evt_storm_update.from_cid = -1
                            # TESTING
                            next_grids = self.game_model.true_xy_to_grid(self.game_model.next_storm_center[0], self.game_model.next_storm_center[1])
                            evt_storm_update.var['cur_center'] = [
                                pack('<h', next_grids[0])[0],
                                pack('<h', next_grids[1])[0],
                                pack('<h', next_grids[2])[0],
                                pack('<h', next_grids[3])[0],
                            ]  # ['\x15', '\x33', '\xa0', '\xa0']  # self.game_model.cur_storm_center
                            evt_storm_update.var['cur_radius'] = self.game_model.next_storm_radius  # ACTUALLY NEXT STORM INFO
                            shrink_speed = float(
                                self.game_model.cur_storm_radius - self.game_model.next_storm_radius) / self.game_model.storm_shrink_duration
                            if self.game_model.storm_pkg_count == 1:
                                shrink_speed = 10000
                            evt_storm_update.var['shrink_speed'] = int(shrink_speed)
                            evt_storm_update.var['time_to_appear_next'] = self.game_model.cur_storm_duration
                            evt_storm_update.var['time_to_shrink'] = self.game_model.storm_shrink_delay
                            self.game_event_manager.broadcast_server_event(evt_storm_update)
                            # print 'center sent:', self.game_model.next_storm_center

                            # set shrink start stamp, otherwise the shrink won't start
                            if self.game_model.storm_pkg_count > 1:  # IF NOT FIRST PACKAGE
                                self.game_model.storm_shrink_start_stamp = time.time() + self.game_model.storm_shrink_delay

                            # print 'storm radius:', self.game_model.cur_storm_radius
                            # print 'time until next storm:', self.game_model.cur_storm_duration
                            # print 'shrink duration:', self.game_model.storm_shrink_duration
                    pass
            except Exception, e:
                print e
            gevent.sleep(GAME_LOGIC_INTERVAL)

    @on_command('spawn_fake_clients')
    def spawn_fake_clients(self, num):
        """
        num == number of fake clients
        :param num:
        :return:
        """
        n = 0
        to_spawn_cid = 0
        while n < num:
            if to_spawn_cid not in self.client_infos:
                self.add_client(to_spawn_cid)
                self.client_infos[to_spawn_cid].state.is_faked = True
                # ['\xa0', '\xa0', 2200]
                self.client_infos[to_spawn_cid].state.pos[2] += n * 50
                grid_x = self.client_infos[to_spawn_cid].state.grid_x
                grid_x = unpack('<h', grid_x + '\x00')[0]
                grid_x += n
                grid_x = pack('<h', grid_x)[0]
                self.client_infos[to_spawn_cid].state.grid_x = grid_x
                # if n == 0:
                #     self.client_infos[to_spawn_cid].state.pos[0] = '\xaa'
                #     self.client_infos[to_spawn_cid].state.grid_x = '\x16'
                # if n == 1:
                #     self.client_infos[to_spawn_cid].state.pos[0] = '\xa0'
                join_evt = EventClientJoinGame()
                join_evt.from_cid = to_spawn_cid
                join_evt.var['car_id'] = 1
                self.on_client_join_game(join_evt)
                to_spawn_cid += 1
                n += 1
        pass

    @on_command('set_storm_enabling')
    def set_storm_enabling(self, storm_flag):
        if storm_flag == 0:
            self.game_model.ENABLE_STORM = False
            print 'storm disabled for room', self.room_id
        else:
            self.game_model.ENABLE_STORM = True
            print 'storm enabled for room', self.room_id


if __name__ == '__main__':
    rs = TinkrGarageRoom(None, 3, 'hh')
    rs.start_server()
    from core.network.net_package import NetPackage
    pkg = NetPackage('?', '3.3.3.3', 10000)
    rs.run_command('handle_package', pkg)
    rs.run_command('add_client', 4)

    shoot_evt = EventClientJoinGame()
    rs.game_event_manager.handle_event(shoot_evt)

    evt = EventClientHit.unpack('\x33\x45\x67\x09\x45\x95\x45\x55\x65\x32\x56\x33\x45\x32\x45\x56\x34\x43\x67\x78')
    time.sleep(1)
    print evt.var
    data = evt.pack()
    print data
    evt = evt.unpack(data)
    print evt.var