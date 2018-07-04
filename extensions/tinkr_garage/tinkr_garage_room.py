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
        state = self.ClientState()
        (pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<iiiiii', state_data)
        state.pos[0] = pos_x
        state.pos[1] = pos_y
        state.pos[2] = pos_z
        state.rot[0] = rot_x
        state.rot[1] = rot_y
        state.rot[2] = rot_z
        return state

    @on_client_game_event(EventClientJoinGame)
    def on_client_join_game(self, evt):
        # login event
        print 'login event'
        vid = evt.var['car_id']
        print 'vehicle id', vid
        token = 0
        login_success = False
        cid = evt.from_cid
        if cid in self.client_infos:
            print 'client', cid, 'already logged in'
        else:
            login_success = True
        if login_success:
            # add client
            new_client_state = self.ClientState()
            # new_client_state.addr = (addr[0], addr[1])
            new_client_state.vid = vid
            new_client_state.spawn_slot = len(self.client_infos)  # cur_spawn_slot

            # notify new client of existing clients
            print 'notify new client of existing clients'
            evt_spawn_old = EventServerSpawnPlayer()
            for existing_cid in self.client_infos:
                evt_spawn_old.from_cid = existing_cid
                evt_spawn_old.var['car_id'] = self.client_infos[existing_cid].state.vid
                evt_spawn_old.var['spawn_slot'] = self.client_infos[existing_cid].state.spawn_slot
                self.game_event_manager.send_server_event(cid, evt_spawn_old)

            # add new client to map
            self.client_infos[cid] = self.ClientInfo(new_client_state)

            # notify all clients to add new client
            print 'notify all clients to add new client'
            evt_spawn_new = EventServerSpawnPlayer()
            evt_spawn_new.from_cid = cid
            evt_spawn_new.var['car_id'] = self.client_infos[cid].vid
            evt_spawn_new.var['spawn_slot'] = self.client_infos[cid].spawn_slot
            # broadcast event
            self.game_event_manager.broadcast_server_event(evt_spawn_new, [])

    @on_client_game_event(EventClientExitGame)
    def on_client_exit_game(self, evt):
        pass




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