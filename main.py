#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys

reload(sys)  
sys.setdefaultencoding('utf8')

import os
import time
import telepot
from peewee import *
from random import choice

if 'OPENSHIFT_DATA_DIR' in os.environ:
    db = SqliteDatabase(os.environ['OPENSHIFT_DATA_DIR']+'datumaro.db')
else:
    db = SqliteDatabase('datumaro.db')

class Parto(Model):
    x = IntegerField()
    y = IntegerField()
    class Meta:
        database = db
class Uzanto(Model):
    uid = IntegerField()
    parto = ForeignKeyField(Parto)
    mono = IntegerField()
    sano = IntegerField()
    nivelo = IntegerField()
    class Meta:
        database = db
class Domo(Model):
    uzanto = ForeignKeyField(Uzanto)
    parto = ForeignKeyField(Parto)
    sano = IntegerField()
    nivelo = IntegerField()
    class Meta:
        database = db
#db.connect()
#db.create_tables([Uzanto, Parto, Domo])

def kreiUrbon(x, y):
    for i in range(0, x):
        for j in range(0, y):
            Parto.create(x = i, y = j)
            
#kreiUrbon(10, 10)

def poz(uzanto_id):
    poz = Parto.select().join(Uzanto).where(Uzanto.uid == uzanto_id).get()
    return int(poz.x), int(poz.y)

#TODO prefetch()
def liberaParto(uzanto_id):
    domoj = Parto.select().join(Domo)
    domojId = []
    for domo in domoj:
        domojId.append(domo.id)
    uzantoDomoj = Domo.select().join(Uzanto).where(Uzanto.uid == uzanto_id)
    uzantoDomojId = []
    for uzantoDomo in uzantoDomoj:
        uzantoDomojId.append(uzantoDomo.parto.id)
    uzantoj = Parto.select().join(Uzanto)
    uzantojId = []
    for uzanto in uzantoj:
        uzantojId.append(uzanto.id)
    for uzantoDomoId in uzantoDomojId:
        domojId.remove(uzantoDomoId)
    liberaParto = Parto.select().where(~(Parto.id << domojId+uzantojId)).order_by(fn.Random()).get()
    return liberaParto.id, liberaParto.x, liberaParto.y

def parto(x, y):
    try:
        domo = Domo.select().join(Parto, on=(Parto.id==Domo.parto)).where(Parto.x==x, Parto.y==y).get()
    except DoesNotExist:
        domo = False
    try:
        uzanto = Uzanto.select().join(Parto).where(Parto.x==x, Parto.y==y).get()
    except DoesNotExist:
        uzanto = False
    return domo, uzanto

def mapi(i0, i1, i2):
    mapoVico = ['', '', '']
    for (x, y, i) in (i0, i1, i2):
        domo, uzanto = parto(x, y)
        mapoVico[i] = x+':'+y
        if domo != False:
            mapoVico[i] += '#'+str(domo.nivelo)
        if uzanto != False:
            mapoVico[i] += '@'+str(uzanto.nivelo)
                
        if domo != False:
            mapoVico[i] += '\n'+str(domo.uzanto.uid)
        elif uzanto != False:
            mapoVico[i] += '\n'+str(uzanto.uid)
    return mapoVico

def rekomenci(uzanto_id):
    uzanto = Uzanto.get(Uzanto.uid == uzanto_id)
    uzanto.mono = 80
    uzanto.parto, x, y = liberaParto(uzanto_id)
    uzanto.nivelo = 1
    uzanto.sano = 10
    Domo.delete().where(Domo.uzanto == uzanto).execute()
    uzanto.save()
    return u'Vi renaskiĝis en %s:%s.' % (x, y)
        
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    m = msg['text']
    maksX, maksY = 9, 9
    if m == u'/start':
        liberaPartoId, x, y = liberaParto(chat_id)
        uzanto, uzantoEstasNova = Uzanto.get_or_create(uid = chat_id, defaults = {'mono':80, 'parto':liberaPartoId, 'nivelo':1, 'sano':10})
        if uzantoEstasNova:
            r = u'Vi naskiĝis en %s:%s.' % (x, y)
        else:
            r = u'Rebonvenon!'
        bot.sendMessage(chat_id, r)
    elif m == u'/restart':
        r = rekomenci(chat_id)
        bot.sendMessage(chat_id, r)
    elif m == u'/poz':
        uzantoX, uzantoY = poz(chat_id)
        r = str(uzantoX) + ':' + str(uzantoY)
        bot.sendMessage(chat_id, r)
    elif m == u'/mono':
        r = Uzanto.get(Uzanto.uid == chat_id).mono
        bot.sendMessage(chat_id, r)
    elif m == u'/domoj':
        r = ''
        uzantoDomoj = Domo.select().join(Uzanto, on=(Domo.uzanto==Uzanto.id)).join(Parto, on=(Domo.parto, Parto.id)).where(Uzanto.uid == chat_id)
        for uzantoDomo in uzantoDomoj:
            r += str(uzantoDomo.parto.x) + ':' + str(uzantoDomo.parto.y) + '#' + str(uzantoDomo.nivelo) + u'~' + str(uzantoDomo.sano) + '\n'
        if r == '':
            r = u'Vi ne havas domon.'
        bot.sendMessage(chat_id, r)
    elif m == u'/domo':
        uzanto = Uzanto.get(Uzanto.uid == chat_id)
        if uzanto.mono >= 2:
            uzantoParto = Parto.select().join(Uzanto).where(Uzanto.uid == chat_id).get()
            domo, domoEstasNova = Domo.get_or_create(uzanto = uzanto, parto = uzantoParto, defaults = {'sano': 10, 'nivelo': 1})
            if not domoEstasNova:
                if uzanto.mono >= (domo.nivelo + 1) * 2:
                    domo.nivelo += 1
                    domo.sano = int(domo.sano * 1.71828)
                    novaNivelo = domo.nivelo
                    domo.save()
                    Uzanto.update(mono = Uzanto.mono - novaNivelo * 2).where(Uzanto.uid == chat_id).execute()
                else:
                    bot.sendMessage(chat_id, u'Vi bezonas monon pli ol (la nivelo de domo) * 2') 
            else:
                Uzanto.update(mono = Uzanto.mono - 2).where(Uzanto.uid == chat_id).execute()
        else:
            bot.sendMessage(chat_id, u'Vi bezonas monon pli ol (la nivelo de domo) * 2')
    elif m == u'/uzanto':
        uzanto = Uzanto.select().join(Parto).where(Uzanto.uid == chat_id).get()
        r = str(uzanto.parto.x) + ':' + str(uzanto.parto.y) + '@' + str(uzanto.nivelo) + '~' + str(uzanto.sano) + '$' + str(uzanto.mono)
        bot.sendMessage(chat_id, r)
    #movi:
    else:
        try:
            try:
                m = m.split('\n')[0]
            except:
                pass
            try:
                m = m.split('@')[0]
            except:
                pass
            try:
                m = m.split('#')[0]
            except:
                pass
            movuX, movuY = m.split(u':')[0:2]
            movuX, movuY = int(movuX), int(movuY)
            uzantoX, uzantoY = poz(chat_id)
            if 0 <= movuX <= maksX and 0 <= movuY <= maksY and (abs(movuX - uzantoX) == 1 or abs(movuX - uzantoX) == 0) and (abs(movuY - uzantoY) == 1 or abs(movuY - uzantoY) == 0):
                try:
                    domo = Domo.select().join(Parto, on=(Parto.id==Domo.parto)).switch(Domo).join(Uzanto).where(Parto.x==movuX, Parto.y==movuY).get()
                except DoesNotExist:
                    domo = ''
                try:
                    uzanto = Uzanto.select().join(Parto).where(Parto.x==movuX, Parto.y==movuY).get()
                except DoesNotExist:
                    uzanto = ''
                laUzanto = Uzanto.get(Uzanto.uid == chat_id)
                if (domo == '' and uzanto == ''):
                    partoId = Parto.get(Parto.x == movuX, Parto.y == movuY).id
                    laUzanto.parto = partoId
                if domo != '':
                    if domo.uzanto.uid == chat_id:
                        partoId = Parto.get(Parto.x == movuX, Parto.y == movuY).id
                        laUzanto.parto = partoId
                if domo != '':
                    if domo.uzanto.uid != chat_id:
                        domo.sano -= laUzanto.nivelo
                        domo.save()
                        if domo.sano <= 0:
                            domo.delete()
                elif uzanto != '':
                    if uzanto.uid != chat_id:
                        uzanto.sano -= laUzanto.nivelo
                        laUzanto.nivelo += 1
                        laUzanto.sano += int(laUzanto.nivelo * 1.71828)
                        laUzanto.mono += laUzanto.nivelo
                        uzanto.save()
                        if uzanto.sano <= 0:
                            r = rekomenci(chat_id)
                            bot.sendMessage(chat_id, u'Vi mortis!\n' + r)
                laUzanto.save()
        except Exception as e:
            print e
        
    uzantoX, uzantoY = poz(chat_id)
    mapo = [mapi((str(uzantoX-1), str(uzantoY-1), 0), (str(uzantoX), str(uzantoY-1), 1), (str(uzantoX+1), str(uzantoY-1), 2)),
            mapi((str(uzantoX-1), str(uzantoY)  , 0), (str(uzantoX), str(uzantoY),   1), (str(uzantoX+1), str(uzantoY)  , 2)),
            mapi((str(uzantoX-1), str(uzantoY+1), 0), (str(uzantoX), str(uzantoY+1), 1), (str(uzantoX+1), str(uzantoY+1), 2))]

    bot.sendMessage(chat_id, u'...', reply_markup={'keyboard':mapo})


TOKEN = '185401678:AAF_7PbchYOIDAKpy6lJqX7z01IsFgDTksA'
bot = telepot.Bot(TOKEN)
bot.message_loop({'chat': on_chat_message})
if __name__ == "__main__":
    while 1:
        time.sleep(10)
