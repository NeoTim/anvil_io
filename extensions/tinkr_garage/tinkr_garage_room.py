from core.room_server_base import *


# client game events
@app_client_game_event
class EventClientJoinGame(ClientGameEvent):
    event_id = '\x00'
    var_struct = [
        ('car_id', 'i')
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


# server game events
@app_server_game_event
class EventServerSpawnPlayer(ServerGameEvent):
    event_id = '\x00'
    var_struct = [
        ('car_id', 'i'),
        ('spawn_slot', 'i')
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


class TinkrGarageRoom(RoomServerBase):

    class ClientState:
        def __init__(self):
            self.pos = [0, 0, 0]
            self.rot = [0, 0, 0]
            self.vid = 0
            self.HP = 100
            self.spawn_slot = 0

    class GameModel:
        def __init__(self):
            pass

    def __init__(self, gate_server_ref, room_id, server_name='tinkr_room'):
        RoomServerBase.__init__(self, gate_server_ref, room_id, server_name)

    def pack_client_state(self, cid):
        state = self.client_infos[cid].state
        return pack('<iiiiii', state.pos[0], state.pos[1], state.pos[2], state.rot[0], state.rot[1], state.rot[2])

    def unpack_client_state(self, state_data):
        """
        NOTE: not specified parameters will be overwritten with default values
        :param state_data:
        :return:
        """
        state = self.ClientState()
        (pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<iiiiii', state_data)
        state.pos[0] = pos_x
        state.pos[1] = pos_y
        state.pos[2] = pos_z
        state.rot[0] = rot_x
        state.rot[1] = rot_y
        state.rot[2] = rot_z
        return state

    def update_client_state(self, cid, new_state):
        self.client_infos[cid].pos = new_state.pos
        self.client_infos[cid].rot = new_state.rot

    @on_client_game_event(EventClientJoinGame)
    def on_client_join_game(self, evt):
        # join game event
        print 'join game event'
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
            self.client_infos[cid].state.spawn_slot = len(self.client_infos)

            # notify new client of existing clients
            print 'notify new client of existing clients'
            evt_spawn_old = EventServerSpawnPlayer()
            for existing_cid in self.client_infos:
                if existing_cid != cid:
                    evt_spawn_old.from_cid = existing_cid
                    evt_spawn_old.var['car_id'] = self.client_infos[existing_cid].state.vid
                    evt_spawn_old.var['spawn_slot'] = self.client_infos[existing_cid].state.spawn_slot
                    self.game_event_manager.send_server_event(cid, evt_spawn_old)

            # add new client to map
            # self.client_infos[cid] = self.ClientInfo(new_client_state)

            # notify all clients to add new client
            print 'notify all clients to add new client'
            evt_spawn_new = EventServerSpawnPlayer()
            evt_spawn_new.from_cid = cid
            evt_spawn_new.var['car_id'] = self.client_infos[cid].state.vid
            evt_spawn_new.var['spawn_slot'] = self.client_infos[cid].state.spawn_slot
            # broadcast event
            self.game_event_manager.broadcast_server_event(evt_spawn_new, [])

            # start game
            evt_start_game = EventServerStartGame()
            evt_start_game.from_cid = -1
            self.game_event_manager.broadcast_server_event(evt_start_game)

    @on_client_game_event(EventClientExitGame)
    def on_client_exit_game(self, evt):
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
        damage = evt.var['damage']
        damage *= 0.96
        print 'client', fire_cid, 'hit', hit_cid, ', damage', damage
        evt_damage = EventServerDamage()
        evt_damage.from_cid = fire_cid
        evt_damage.var['fire_cid'] = fire_cid
        evt_damage.var['damage'] = damage
        self.game_event_manager.broadcast_server_event(evt_damage)

    @on_client_game_event(EventClientPickUpWeapon)
    def on_client_pick_up_weapon(self, evt):
        # pick up weapon event
        print 'pick up weapon event'
        weapon_id = evt.var['weapon_id']
        weapon_type = evt.var['weapon_type']
        equip_slot = evt.var['equip_slot']

        pick_success = True

        if pick_success:

            # destroy weapon event
            evt_destroy_weapon = EventServerDestroyWeapon()
            evt_destroy_weapon.from_cid = evt.from_cid
            evt_destroy_weapon.var['weapon_id'] = weapon_id
            self.game_event_manager.broadcast_server_event(evt_destroy_weapon)

            # equip weapon event
            evt_equip_weapon = EventServerEquipWeapon()
            evt_equip_weapon.from_cid = evt.from_cid
            evt_equip_weapon.var['weapon_id'] = weapon_id
            evt_equip_weapon.var['weapon_type'] = weapon_type
            evt_equip_weapon.var['equip_slot'] = equip_slot
            self.game_event_manager.broadcast_server_event(evt_equip_weapon)


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