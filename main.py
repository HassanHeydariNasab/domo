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
import gettext
from math import log

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
    lingvo = CharField(default='eo')
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

def traduki(uzanto_id):
    locale = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
    gettext.install('uzanta', locale, unicode=True)
    try:
        lingvo = Uzanto.get(Uzanto.uid == uzanto_id).lingvo
        traduko = gettext.translation('uzanta', locale, languages=[lingvo])
        global _
        _ = traduko.ugettext
        traduko.install()
    except:
        pass
#print _(u'nur por testado celoj.')

def kreiUrbon(x, y):
    for i in range(0, x):
        for j in range(0, y):
            Parto.create(x = i, y = j)
            
#kreiUrbon(10, 10)
global maksX
global maksY
maksX, maksY = 9, 9

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
        if int(x) > maksX or int(y) > maksY or int(x) < 0 or int(y) < 0:
            mapoVico[i] = '*'
        else:
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
    traduki(uzanto_id)
    uzanto = Uzanto.get(Uzanto.uid == uzanto_id)
    uzanto.mono = 80
    uzanto.parto, x, y = liberaParto(uzanto_id)
    uzanto.nivelo = 1
    uzanto.sano = 60
    Domo.delete().where(Domo.uzanto == uzanto).execute()
    uzanto.save()
    return _(u'Vi renaskiĝis en %(poz)s.') % {'poz':str(x)+':'+str(y)}

def Tutmapi(uzanto_id):
    uzantoX, uzantoY = poz(uzanto_id)
    mapo = [mapi((str(uzantoX-1), str(uzantoY-1), 0), (str(uzantoX), str(uzantoY-1), 1), (str(uzantoX+1), str(uzantoY-1), 2)),
            mapi((str(uzantoX-1), str(uzantoY)  , 0), (str(uzantoX), str(uzantoY),   1), (str(uzantoX+1), str(uzantoY)  , 2)),
            mapi((str(uzantoX-1), str(uzantoY+1), 0), (str(uzantoX), str(uzantoY+1), 1), (str(uzantoX+1), str(uzantoY+1), 2))]
    return mapo

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    m = msg['text']
    ms = m.split('@')
    mss = m.split(' ')
    mapota = True
    traduki(chat_id)
    if m == u'/start':
        liberaPartoId, x, y = liberaParto(chat_id)
        uzanto, uzantoEstasNova = Uzanto.get_or_create(uid = chat_id, defaults = {'mono':80, 'parto':liberaPartoId, 'nivelo':1, 'sano':60})
        if uzantoEstasNova:
            r = u'Elektu lingvon:\nSelect a language:\nزبانی را برگزینید:'
            lingvoj = [['/lingvo Esperanto'], ['/lingvo English'], ['/lingvo فارسی']]
            bot.sendMessage(chat_id, r, reply_markup={'keyboard':lingvoj})
            mapota = False
        else:
            r = _(u'Rebonvenon!')
            bot.sendMessage(chat_id, r)
    elif len(mss) == 2 and m[:7] == '/lingvo':
        if mss[1] == 'eo' or mss[1] == 'Esperanto' or mss[1] == 'esperanto':
            lingvo = 'eo'
        elif mss[1] == 'en' or mss[1] == 'English' or mss[1] == 'english':
            lingvo = 'en_US'
        elif mss[1] == 'fa' or mss[1] == 'فارسی' or mss[1] == 'farsi' or mss[1] == 'Farsi' or mss[1] == 'Persian' or mss[1] == 'persian':
            lingvo = 'fa'
        else:
            lingvo = 'eo'
        Uzanto.update(lingvo = lingvo).where(Uzanto.uid == chat_id).execute()
        traduki(chat_id)
        mapo = Tutmapi(chat_id)
        x, y = poz(chat_id)
        r = _(u'La lingvo ŝanĝis.\nVi estas en %(poz)s') % {u'poz': str(x)+':'+str(y)}
        bot.sendMessage(chat_id, r, reply_markup={'keyboard':mapo})
        mapota = False

    elif m == u'/helpo':
        r = _(u'''\
Krado estas ludo pri la domoj kaj la homoj.
La homoj kreas domojn. ili atakas aliajn homojn kaj domojn.
Ŝtelu la monojn kaj neniigu la domojn!
Promociu viajn domojn kaj ataku al la atenculoj!

Mapo montriĝas Malsupre. klaku ĝiajn klavojn por movi aŭ ataki. vi estas en mezo de la mapo.

• La difino de la signoj de la ludo:
4:8 estas pozicio tia x:y
773626641 estas Telegrama ID-o de vi aŭ aliulo
@7 estas homo je 7-a nivelo
#3 estas domo je 3-a nivelo
~26 estas sano de vi aŭ via domo
$33 estas mono ke vi havas
* estas ekster la mondo!

Nur faru tion vi volas fari!
• Jen la komandoj:
/uzanto - montri informojn pri vi
/domoj - montri la domojn ke vi havas
/domo - krei aŭ promocii domon
/rekomenci - rekomenci la ludon
/helpo - montri ĉi-tion helpon

• Ĝia kodo estas tie libere:
https://github.com/HassanHeydariNasab/domo\
        ''')
        bot.sendMessage(chat_id, r)
    elif m == u'/rekomenci':
        r = rekomenci(chat_id)
        bot.sendMessage(chat_id, r)
    elif m == u'/domoj':
        r = ''
        uzantoDomoj = Domo.select().join(Uzanto, on=(Domo.uzanto==Uzanto.id)).join(Parto, on=(Domo.parto, Parto.id)).where(Uzanto.uid == chat_id)
        for uzantoDomo in uzantoDomoj:
            r += str(uzantoDomo.parto.x) + ':' + str(uzantoDomo.parto.y) + '#' + str(uzantoDomo.nivelo) + u'~' + str(uzantoDomo.sano) + '\n'
        if r == '':
            r = _(u'Vi ne havas domon.')
        bot.sendMessage(chat_id, r)
    elif m == u'/domo':
        uzanto = Uzanto.get(Uzanto.uid == chat_id)
        if uzanto.mono >= 2:
            uzantoParto = Parto.select().join(Uzanto).where(Uzanto.uid == chat_id).get()
            domo, domoEstasNova = Domo.get_or_create(uzanto = uzanto, parto = uzantoParto, defaults = {'sano': 30, 'nivelo': 1})
            if not domoEstasNova:
                if uzanto.mono >= (domo.nivelo + 1) * 2:
                    domo.nivelo += 1
                    domo.sano = int(domo.sano + log(domo.sano * (domo.nivelo) + 20, 2.718281828459045))
                    novaNivelo = domo.nivelo
                    domo.save()
                    Uzanto.update(mono = Uzanto.mono - novaNivelo * 2).where(Uzanto.uid == chat_id).execute()
                else:
                    bot.sendMessage(chat_id, _(u'Por atingi domon je la nivelo de %(nivelo)s, vi devas havi %(mono)d monon.') % {'nivelo': domo.nivelo + 1, 'mono': (domo.nivelo + 1) * 2})
            else:
                Uzanto.update(mono = Uzanto.mono - 2).where(Uzanto.uid == chat_id).execute()
        else:
            bot.sendMessage(chat_id, _(u'Vi bezonas almenaŭ 2 monon por fari domon.'))
    elif m == u'/uzanto':
        uzanto = Uzanto.select().join(Parto).where(Uzanto.uid == chat_id).get()
        r = str(uzanto.parto.x) + ':' + str(uzanto.parto.y) + '@' + str(uzanto.nivelo) + '~' + str(uzanto.sano) + '$' + str(uzanto.mono)
        bot.sendMessage(chat_id, r)
    elif m == u'/uzantoj' and chat_id == 170378225:
        r = ''
        uzantoj = Uzanto.select().join(Parto)
        r += str(uzantoj.count()) + ' uzantoj.\n'
        for uzanto in uzantoj:
            domoj = Domo.select().join(Uzanto).where(Uzanto.id == uzanto.id).count()
            r += str(uzanto.parto.x) + ':' + str(uzanto.parto.y) + '@' + str(uzanto.nivelo) + '~' + str(uzanto.sano) + '$' + str(uzanto.mono) + ' --- ' + str(domoj) + '# ' + '/domoj@' + str(uzanto.uid) + ' --- /uzanto@' + str(uzanto.uid) + '\n'
        bot.sendMessage(chat_id, r)
    elif len(ms) == 2 and (ms[0] == '/domoj' or ms[0] == '/uzanto' or ms[0] == '/forigi') and chat_id == 170378225:
        if ms[0] == u'/domoj':
            r = ''
            uzantoDomoj = Domo.select().join(Uzanto, on=(Domo.uzanto==Uzanto.id)).join(Parto, on=(Domo.parto, Parto.id)).where(Uzanto.uid == int(ms[1]))
            for uzantoDomo in uzantoDomoj:
                r += str(uzantoDomo.parto.x) + ':' + str(uzantoDomo.parto.y) + '#' + str(uzantoDomo.nivelo) + u'~' + str(uzantoDomo.sano) + '\n'
            if r == '':
                r = _(u'La uzanto ne havas domon.')
            bot.sendMessage(chat_id, r)
        elif ms[0] == u'/uzanto':
             babilo = bot.getChat(int(ms[1]))
             r = ''
             try:
                 r += '@' + babilo['username']
                 r += '  ' + babilo['first_name']
                 r += ' ' + babilo['last_name']
             except:
                 pass
             bot.sendMessage(chat_id, r)
        elif ms[0] == u'/forigi':
            try:
                uzanto = Uzanto.get(Uzanto.uid == int(ms[1]))
                Domo.delete().where(Domo.uzanto == uzanto).execute()
                Uzanto.delete().where(Uzanto.uid == int(ms[1])).execute()
                bot.sendMessage(chat_id, _(u'La uzanto kaj liaj domoj foriĝis.'))
            except Exception as e:
                print e
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
                        informojPriLaDomo = str(domo.parto.x) + ':' + str(domo.parto.y) + '#' + str(domo.nivelo) + u'~' + str(domo.sano)
                        if domo.sano >= laUzanto.nivelo:
                            laUzanto.mono += laUzanto.nivelo
                            domo.sano -= laUzanto.nivelo
                        else:
                            laUzanto.mono += domo.sano
                            domo.sano = 0
                        domo.save()
                        if domo.sano <= 0:
                            domo.delete_instance()
                            mapo = Tutmapi(uzanto.uid)
                            bot.sendMessage(uzanto.uid, _(u'Via domo, %(domo)s, neniiĝis!') % {'domo':informojPriLaDomo}, reply_markup={'keyboard':mapo})
                        else:
                            informojPriLaDomo = str(domo.parto.x) + ':' + str(domo.parto.y) + '#' + str(domo.nivelo) + u'~' + str(domo.sano)
                            bot.sendMessage(chat_id, informojPriLaDomo)
                elif uzanto != '':
                    if uzanto.uid != chat_id:
                        informojPriLaUzanto = str(uzanto.parto.x) + ':' + str(uzanto.parto.y) + '@' + str(uzanto.nivelo) + '~' + str(uzanto.sano) + '$' + str(uzanto.mono)
                        uzanto.sano -= laUzanto.nivelo
                        laUzanto.sano += int(laUzanto.nivelo * 1.142)
                        if uzanto.mono >= laUzanto.nivelo * 2:
                            laUzanto.mono += laUzanto.nivelo * 2
                            uzanto.mono -= laUzanto.nivelo * 2
                        else:
                            laUzanto.mono += uzanto.mono
                            uzanto.mono = 0
                        laUzanto.nivelo += 1
                        uzanto.save()
                        if uzanto.sano <= 0:
                            r = rekomenci(uzanto.uid)
                            mapo = Tutmapi(uzanto.uid)
                            bot.sendMessage(uzanto.uid, _(u'Vi, %(uzanto)s, mortis!\n') % {'uzanto':informojPriLaUzanto} + r, reply_markup={'keyboard':mapo})
                        else:
                            informojPriLaUzanto = str(uzanto.parto.x) + ':' + str(uzanto.parto.y) + '@' + str(uzanto.nivelo) + '~' + str(uzanto.sano)
                            bot.sendMessage(chat_id, informojPriLaUzanto)
                laUzanto.save()
        except Exception as e:
            print e
    if mapota:
        mapo = Tutmapi(chat_id)
        bot.sendMessage(chat_id, u'...', reply_markup={'keyboard':mapo})

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if sys.argv[1] == 'd':
            TOKEN = '185401678:AAF_7PbchYOIDAKpy6lJqX7z01IsFgDTksA'
    else:
        o = open(os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'domo'))
        t = o.read()
        TOKEN = t[:-1]
        o.close()
    bot = telepot.Bot(TOKEN)
    bot.message_loop({'chat': on_chat_message})

    while 1:
        time.sleep(10)
