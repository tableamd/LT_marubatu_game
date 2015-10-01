#encoding:utf-8
"""
websocketの概要について

"""

from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session, request, render_template, send_from_directory
from flask.ext.socketio import SocketIO, emit, join_room, leave_room
import uuid
import re

UPLOADDIR = "templates"
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'this_is_secret_key_!'
socketio = SocketIO(app)

#thread = None

clients = []
goban = []
num_where = [2, 8, 14, 23, 29, 35, 43, 47, 51]
a = u"__1__|__2__|__3__<br>__4__|__5__|__6__<br>　7　|　8　|　9　"
font = "<font color='red'>%s</font>"
h2 = "<h2>%s</h2>"


def num_checker(num):
    if num%2:
        return (num-1)/2
    else:
        return num/2


def get_index(clients,i):
    n = 0
    for num,uid in enumerate(clients):
        if i in uid:
            n = num
    return n


def who_win(go):
    #x->3 o->5
    data = ""
    for val in num_where:
        data += go[val]
    #print data
    d = re.sub(r"x","3",re.sub(r"o","5",re.sub(r"[1-9]","0",data)))
    n = [int(v) for v in d]
    l = []
    l.append(n[0]+n[1]+n[2]);l.append(n[3]+n[4]+n[5]);l.append(n[6]+n[7]+n[8])
    l.append(n[0]+n[3]+n[6]);l.append(n[1]+n[4]+n[7]);l.append(n[2]+n[5]+n[8])
    l.append(n[0]+n[4]+n[8]);l.append(n[2]+n[4]+n[6])
    for num in l:
        if num == 9:
            return "x"
        if num == 15:
            return "o"
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/view_upload/<path:filename>")
def view_upload(filename):
    return send_from_directory(UPLOADDIR, filename)

@socketio.on('my event', namespace='/test')
def test_message(message):

    emit('my response',
         {'data': message["data"]})


@socketio.on('my broadcast event', namespace='/test')
def test_message2(message):

    try:
        index = get_index(clients, message["from"])
        index2 = clients[index].index(session["id"])
    except:
        return

    masu = str(message["masu"])
    koma = message["mykoma"]
    goban[index] = goban[index].replace(masu,koma)
    win = who_win(goban[index])
    a = 0 if index2==1 else 1

    for sessid, socket in request.namespace.socket.server.sockets.items():
        try:
            if socket["/test"].session["id"] == clients[index][a]:
                socket["/test"].base_emit("my response",
                                         {"data" : h2%goban[index],
                                          "me" : 1,
                                          "masu" : str(int(message["masu"])+1),
                                          "win" : 0 if not win else win})
                emit("my response",
                     {"data" : h2%goban[index],
                      "masu" : str(int(message["masu"])+1),
                      "me" : 0,
                      "win" : 0 if not win else win})
        except:
            pass


@socketio.on('connect', namespace='/test')
def test_connect():
    #print "hogehoge"
    #emit('my response', {'data': 'Connected', 'count': 0})

    if not session.get("id", None):
        session["id"] = str(uuid.uuid4())

    l = len(clients)-1

    if l == -1 or len(clients[l]) == 2:
        clients.append([session["id"]])
        session["koma"] = "o"
        goban.append(a)
        emit('my response',{"data":"相手の接続を待機しています","win":0})
    elif len(clients[l]) == 1:
        clients[l].append(session["id"])
        session["koma"] = "x"
        emit('my response',{"data":h2%a,"win":0})

    emit('first_connect',{"id" : session["id"],"koma" : session["koma"]})



@socketio.on('disconnect', namespace='/test')
def test_disconnect():

    #print('Client disconnected')

    try:
        index = get_index(clients, session["id"])
        index2 = clients[index].index(session["id"])
    except:
        return

    a = 0 if index2==1 else 1

    for sessid, socket in request.namespace.socket.server.sockets.items():
        try:
            if socket["/test"].session["id"] == clients[index][a]:
                socket["/test"].base_emit("my response",
                                         {"data":"相手の接続が切れました", 
                                          "win" : socket["/test"].session["koma"]})
        except:
            pass
    del clients[index]
    del goban[index]

if __name__ == '__main__':
    socketio.run(app,transports=['websocket'],close_timeout=10)
