# tokenkeycode.py というファイル名で以下の行を保存する 
# TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxx.yyyyyy.zzzzzzzzzzzzzzzzzzzzzzzzzzz'

inputchannel = '凸報告'
outputchannel = '状況報告'

BossName = [
    'ゴブリングレート',
    'ライライ',
    'シードレイク',
    'スピリットホーン',
    'カルキノス',
]

#最大攻撃数
MAX_SORITE = 3

BATTLEPRESTART = '06/24'
BATTLESTART = '06/25'
BATTLEEND = '06/29'

CmdAttack = ['凸', 'a']
CmdTaskkill = ['タスキル', 'taskkill']

LevelUpLap = [4, 11, 35]
BossHpData = [
    [   [600, 1.2], [800, 1.2], [1000, 1.3], [1200, 1.4], [1500, 1.5]   ],
    [   [600, 1.6], [800, 1.6], [1000, 1.8], [1200, 1.9], [1500, 2.0],  ],
    [   [700, 2.0], [900, 2.0], [1300, 2.4], [1500, 2.4], [2000, 2.6],  ],
    [   [1500, 3.5], [1600, 3.5], [1800, 3.7], [1900, 3.8], [2000, 4.0], ],
]

GachaLotData = [
    [0.7, 0.0, 1.8, 18, 100], # 通常
    [0.7, 0.0, 1.8, 18, 100], # 限定
    [0.7, 0.0, 1.8, 18, 100], # プライズ
    [1.4, 0.0, 3.6, 18, 100], # 通常(2倍)
    [0.7, 0.9, 3.4, 18, 100], # プリフェス
]

PrizeGacha = False

ERRFILE = 'error.log'
SETTINGFILE = 'setting.json'

#---設定ここまで---

BossLapScore = []
for l in BossHpData:
    lapscore = 0
    for i in l:
        lapscore += i[0] * i[1]
        i.append(i[0] * i[1])
    BossLapScore.append(lapscore)

GachaData = []

import tokenkeycode

import asyncio
import discord
from discord.ext import tasks
import datetime 
import json
import glob
import os
import codecs
import random
from typing import List, Dict, Any, Optional
from io import StringIO
#from PIL import Image
#import numpy as np

BOSSNUMBER = len(BossName)

class GachaRate():
    def __init__(self, rate, star, namelist):
        self.rate = rate
        self.star = star
        self.namelist = namelist

class PrizeRate():
    def __init__(self, rate, star, memorial, stone, heart):
        self.rate = rate
        self.star = star
        self.memorial = memorial
        self.stone = stone
        self.heart = heart
    
    def Name(self):
        return str(7 - self.star) + '等'

class Princess():
    def __init__(self, name, star):
        self.name = name
        self.star = star

class GachaSchedule:
    def __init__(self, startdate, gachatype, name):
        self.startdate = startdate
        self.gachatype = gachatype
        self.name = name
    
    def Serialize(self):
        ret = {}
        ignore = []

        for key, value in self.__dict__.items():
            if not key in ignore:
                ret[key] = value

        return ret

    @staticmethod
    def Deserialize(dic):
        result = GachaSchedule('', '', '')
        for key, value in dic.items():
            result.__dict__[key] = value
        return result


class GlobalStrage:
    @staticmethod
    def SerializeList(data):
        result = []
        for d in data:
            result.append(d.Serialize())
        return result

    @staticmethod
    def Load():
        global GachaData
        global BossName
        global BATTLESTART
        global BATTLEEND

        with open(SETTINGFILE) as a:
            mdic =  json.load(a)

            if ('GachaData' in mdic):
                gdata = []
                for m in mdic['GachaData']:
                    gdata.append(GachaSchedule.Deserialize(m))

                GachaData = gdata

            if ('BossName' in mdic):
                BossName = mdic['BossName']

            if ('BATTLESTART' in mdic):
                BATTLESTART = mdic['BATTLESTART']

            if ('BATTLEEND' in mdic):
                BATTLEEND = mdic['BATTLEEND']

    @staticmethod
    def Save():
        GachaDataSerialize = []
        for m in GachaData:
            GachaDataSerialize.append(m.Serialize())

        dic = {
            'GachaData': GachaDataSerialize,
            'BossName' : BossName,
            'BATTLESTART' : BATTLESTART,
            'BATTLEEND' : BATTLEEND,
        }

        with open(SETTINGFILE, 'w') as a:
            json.dump(dic, a , indent=4)

class Gacha():
    def __init__(self):
        self.gachabox = None
        self.limitdate = '2000/01/01 00:00:00'
        self.gachatype = '3'
        self.prize = False

    def GachaSave(self):
        pname =  ['コッコロ(プリンセス)', 'ペコリーヌ(プリンセス)', 'クリスティーナ', 'ムイミ', 'ネネカ']
        s3name = ['マコト','キョウカ','トモ','ルナ','カスミ','ジュン','アリサ','アン','クウカ(オーエド)',
                'ニノン(オーエド)','ミミ(ハロウィン)','ルカ','クロエ','イリヤ','アンナ','グレア','カヤ',
                'イリヤ(クリスマス)','カスミ(マジカル)','ノゾミ','マホ','シズル','サレン','ジータ','ニノン',
                'リノ','アキノ','モニカ','イオ','ハツネ','アオイ(編入生)','ユニ','チエル','リン(レンジャー)',
                'マヒル(レンジャー)','リノ(ワンダー)','イノリ']
        s2name = ['カオリ','ナナカ','エリコ','シオリ','ミミ','タマキ','マツリ','スズナ','ミヤコ','クウカ',
                'アカリ','ミツキ','ツムギ','ミサト','アヤネ','シノブ','チカ','ミフユ','リン','ユキ','マヒル']
        s1name = ['レイ','ヨリ','ヒヨリ','リマ','ユカリ','クルミ','ミソギ','スズメ','アユミ','アオイ']
        global GachaData

        GachaData = []
        for n in s3name:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', '3', n))

        for n in s2name:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', '2', n))

        for n in s1name:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', '1', n))

        for n in pname:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', 'f', n))

        GachaData.append(GachaSchedule('2020/06/24 12:00:00', 'p', 'クリスティーナ(クリスマス)'))
        GachaData.append(GachaSchedule('2020/06/30 12:00:00', 'f', 'ユイ(プリンセス)'))

        GlobalStrage.Save()

    def GetBox(self) -> List[GachaRate]:
        global PrizeGacha

        datetime_format = datetime.datetime.now()
        datestr = datetime_format.strftime("%Y/%m/%d %H:%M:%S")  # 2017/11/12 09:55:28

        gachabox : List[GachaRate] = [
            GachaRate(1.8, 3, ['マコト','キョウカ','トモ','ルナ','カスミ','ジュン','アリサ','アン','クウカ(オーエド)','ニノン(オーエド)','ミミ(ハロウィン)','ルカ','クロエ','イリヤ','アンナ','グレア','カヤ','イリヤ(クリスマス)','カスミ(マジカル)','ノゾミ','マホ','シズル','サレン','ジータ','ニノン','リノ','アキノ','モニカ','イオ','ハツネ','アオイ(編入生)','ユニ','チエル','リン(レンジャー)','マヒル(レンジャー)','リノ(ワンダー)']),
            GachaRate(18, 2, ['カオリ','ナナカ','エリコ','シオリ','ミミ','タマキ','マツリ','スズナ','ミヤコ','クウカ','アカリ','ミツキ','ツムギ','ミサト','アヤネ','シノブ','チカ','ミフユ','リン','ユキ','マヒル']),
            GachaRate(100, 1, ['レイ','ヨリ','ヒヨリ','リマ','ユカリ','クルミ','ミソギ','スズメ','アユミ','アオイ']),
        ]

        if (datestr < '2020/04/24 12:00:00'):
            PrizeGacha = False
            return [
                GachaRate(0.7, 3, ['チエル Pickup!']),
                ] + gachabox

        if (datestr < '2020/04/30 12:00:00'):
            PrizeGacha = True
            return [
                GachaRate(0.7, 3, ['キョウカ(ハロウィン) Pickup!']),
                ] + gachabox

        if (datestr < '2020/05/10 12:00:00'):
            PrizeGacha = False
            return [
                GachaRate(0.7, 3, ['リン(レンジャー) Pickup!']),
                ] + gachabox

        if (datestr < '2020/05/15 12:00:00'):
            PrizeGacha = True
            return [
                GachaRate(0.7, 3, ['クウカ(オーエド) Pickup!','ニノン(オーエド) Pickup!']),
                ] + gachabox

        if (datestr < '2020/05/31 12:00:00'):
            PrizeGacha = False
            return [
                GachaRate(0.7, 3, ['マヒル(レンジャー) Pickup!']),
                ] + gachabox

        if (datestr < '2020/06/03 19:00:00'):
            PrizeGacha = False
            return [
                GachaRate(0.7, 3, ['コッコロ(プリンセス) Pickup!']),
                GachaRate(0.9, 3, ['ペコリーヌ(プリンセス) PriFes!',
                'クリスティーナ PriFes!', 'ムイミ PriFes!', 'ネネカ PriFes!']),
                GachaRate(3.4, 3, gachabox[0].namelist),
                gachabox[1],
                gachabox[2]
                ] 

        if (datestr < '2020/06/10 12:00:00'):
            PrizeGacha = False
            return [
                GachaRate(0.7, 3, ['リノ(ワンダー) Pickup!']),
                ] + gachabox

        if (datestr < '2020/06/17 15:00:00'):
            PrizeGacha = True
            return [
                GachaRate(0.7, 3, ['スズナ(サマー) Pickup!','サレン(サマー) Pickup!']),
                ] + gachabox

        if (datestr < '2020/06/30 12:00:00'):
            PrizeGacha = False
            return [
                GachaRate(0.7, 3, ['イノリ Pickup!']),
                ] + gachabox

        PrizeGacha = False
        return gachabox

    @staticmethod
    def typetoindex(c) -> int:
        if (c == 'l'): return 0
        if (c == 'p'): return 0
        if (c == 'f'): return 1
        if (c == '3'): return 2
        if (c == '2'): return 3
        if (c == '1'): return 4
        return -1
        
    def PickUpDelete(self, name):
        if type(name) is list:
            for m in name:
                self.PickUpDelete(m)
        
        for gacharate in self.gachabox:
            if name in gacharate.namelist:
                gacharate.namelist.remove(name)

    def Decorate(self):
        for i in range(len(self.gachabox[0].namelist)):
            self.gachabox[0].namelist[i] += ' PicuUp!'

        for i in range(len(self.gachabox[1].namelist)):
            self.gachabox[1].namelist[i] += ' PriFes!'

    def GetBoxData(self) -> List[GachaRate]:
        datetime_format = datetime.datetime.now()
        datestr = datetime_format.strftime("%Y/%m/%d %H:%M:%S")  # 2017/11/12 09:55:28

        if self.limitdate == None and GachaData[-1].startdate <= datestr:
            return self.gachabox

        if datestr < self.limitdate:
            return self.gachabox

        self.limitdate = None
        pickup = None
        self.gachabox : List[GachaRate] = [
            GachaRate(0.0, 3, []),
            GachaRate(0.0, 3, []),
            GachaRate(0.0, 3, []),
            GachaRate(0.0, 2, []),
            GachaRate(0.0, 1, []),
        ]

        for m in GachaData:
            if datestr < m.startdate:
                self.limitdate = m.startdate
                break

            pickup = m
            n = self.typetoindex(m.gachatype)
            if 0 < n:
                self.gachabox[n].namelist.append(m.name)

        self.PickUpDelete(pickup.name)
        self.gachabox[0].namelist.append(pickup.name)
        self.Decorate()

        lot = GachaLotData[0]
        if pickup.gachatype == 'l': lot = GachaLotData[1]
        if pickup.gachatype == 'p': lot = GachaLotData[2]
        if pickup.gachatype == 'd': lot = GachaLotData[3]
        if pickup.gachatype == 'f': lot = GachaLotData[4]

        for m in range(len(lot)):
            self.gachabox[m].rate = lot[m]

        if pickup.gachatype == 'p': self.prize = True
        else: self.prize = False

        self.gachatype = pickup.gachatype

        return self.gachabox

    @staticmethod
    def NameListToString(namelist):
        if type(namelist) is str: 
            return namelist
        if type(namelist) is list:
            return ','.join(namelist)
        return ''

    def ToString(self):
        self.GetBoxData()

        message = ''
        message += '%s %s\n' % (self.gachatype, GachaData[-1].startdate)

        for rate in self.gachabox:
            message += '%f %d %s len:%d\n' % (rate.rate, rate.star, rate.namelist[-1], len(rate.namelist) )

        return message

    @staticmethod
    def GachaScheduleData():
        message = ''
        num = 0
        for m in reversed(GachaData):
            if 5 <= num or m.startdate <= '2000/01/01 00:00:00':
                break
            message +=  '%d: %s %s %s\n' % (num + 1, m.gachatype, m.startdate, Gacha.NameListToString(m.name) )
            num += 1
        
        return message

    @staticmethod
    def Lottery(box, leaststar = 1):
        rndstar = random.random() * 100
        before = None
        for b in box:
            if b.star < leaststar:
                return before

            if rndstar <= b.rate:
                return b

            rndstar -= b.rate
            before = b

    @staticmethod
    def LotteryPrincess(box : List[GachaRate], leaststar = 1) -> Princess:

        b = Gacha.Lottery(box, leaststar)
        p = random.randint(0, len(b.namelist) - 1)
        return Princess(b.namelist[p], b.star)

    @staticmethod
    def LotteryPrize(leaststar = 1) -> PrizeRate:
        box = [
            PrizeRate(0.5, 6, 40, 5, 5),
            PrizeRate(  1, 5, 20, 5, 3),
            PrizeRate(  5, 4,  5, 1, 3),
            PrizeRate( 10, 3,  1, 1, 2),
            PrizeRate(23.5,2,  0, 1, 1),
            PrizeRate(100, 1,  0, 1, 0),
        ]

        return Gacha.Lottery(box, leaststar)

gacha = Gacha()

#クランスコア計算ロジック

class CranScore:
    @staticmethod
    def Calc(score):
        total = 0
        level = 0
        while level < len(LevelUpLap):
            prevlap = (LevelUpLap[level - 1] if 0 < level else 1)
            blap = LevelUpLap[level] - prevlap
            if score < total + blap * BossLapScore[level]:
                break
            total += blap * BossLapScore[level]
            level += 1
        
        lap = (score - total) // BossLapScore[level] + (LevelUpLap[level - 1] if 0 < level else 1)
        modscore = (score - total) % BossLapScore[level]

        totalscore = 0
        bindex = 0
        while bindex < BOSSNUMBER:
            nowbossscore = BossHpData[level][bindex][2]

            if modscore < totalscore + nowbossscore:
                hprate = int(100 - (modscore - totalscore) * 100 // nowbossscore)

                return type("ScoreCalcResult", (object,), {
                    "lap": lap,
                    "level": level,
                    "bossindex": bindex,
                    "hprate" : hprate,
                    "modscore" : modscore
                })
            totalscore += nowbossscore
            bindex += 1

        return None

#討伐データ収集
class DefeatData:
    def __init__(self, defeattime, name):
        self.defeattime = defeattime
        self.name = name
    
    def Serialize(self):
        ret = {}
        ignore = []

        for key, value in self.__dict__.items():
            if not key in ignore:
                ret[key] = value

        return ret

    @staticmethod
    def Deserialize(dic):
        result = DefeatData('', '')
        for key, value in dic.items():
            result.__dict__[key] = value
        return result


def Command(str, cmd):
    if (isinstance(cmd, list)):
        for c in cmd:
            ret = Command(str, c)
            if (ret is not None):
                return ret
        return None

    length = len(cmd)
    if (str[:length] == cmd):
        return str[length:].strip()
    return None

class CranMember():

    def __init__(self):
        self.attack = False
        self.attacktime = None
        self.name = ''
        self.taskkill = 0
        self.history : List[Dict[str, Any]] = []
        self.boss = 0
        self.notice = None
        self.mention = ''
        self.gacha = 0
        self.attackmessage = None

    def CreateHistory(self, messageid, bosscount, overtime, defeat):
        self.history.append(
            {
                'messageid': messageid,
                'bosscount': bosscount,
                'overtime': overtime,
                'defeat' : defeat,
                'memo' : '',
                'other' : [],
            }
        )


    def Attack(self, cran, renewal = True):
        self.attack = True
        self.attacktime = datetime.datetime.now()

        if (renewal):
            self.boss = cran.bosscount

    def SortieCount(self):
        count = 0
        for h in self.history:
            if (h['overtime'] == 0):
                 count += 1
        if (MAX_SORITE <= count):
            return MAX_SORITE
        return count

    def Finish(self, cran, messageid, defeat = False):
        self.attack = False
        self.attacktime = None
        self.CreateHistory(messageid, self.boss, 0, defeat)
    
    def Cancel(self, cran):
        self.attack = False
        self.attacktime = None

    def Overkill(self, cran, overtime, messageid):
        self.attack = False
        self.attacktime = None
        self.CreateHistory(messageid, self.boss, overtime, True)
    
    def Overtime(self):
        if (len(self.history) == 0): return 0
        return self.history[-1]['overtime']

    def Overboss(self):
        if (len(self.history) == 0): return -1
        return self.history[-1]['bosscount']

    def Lastmessageid(self):
        if (len(self.history) == 0): return 0
        return self.history[-1]['messageid']

    def Memo(self):
        if (len(self.history) == 0): return ''
        if ('memo' in self.history[-1]):
            return self.history[-1]['memo']
        return ''

    def SetMemo(self, memostr):
        if (len(self.history) == 0): return
        self.history[-1]['memo'] = memostr.strip()

    def IsOverkill(self):
        return self.Overtime() != 0
    
    def MessageChcck(self, messageid):
        for h in self.history:
            if (h['messageid'] == messageid):
                return True
        return False

    def Reset(self):
        self.attack = False
        self.attacktime = None
        self.taskkill = 0
        self.history = []
        self.notice = None
        self.gacha = 0

    async def History(self, message):
        str = ''
        count = 1
        for h in self.history:
            str += '%d回目 %d周目:%s' % (count,
            h['bosscount'] // BOSSNUMBER + 1, 
            BossName[h['bosscount'] % BOSSNUMBER])

            if (h['defeat']):
                str += ' %d秒' % (h['overtime'])

            str += '\n'

            if (h['overtime'] == 0):
                count += 1
        if (str == '' ): str = '履歴がありません'
        await message.channel.send(str)

    def SetNotice(self, bossstr):
        try:
            boss = int(bossstr)
            if (boss <= 0 or BOSSNUMBER < boss):
                self.notice = None
            else:
                self.notice = boss
        except ValueError:
            pass

    def Serialize(self):
        ret = {}
        ignore = ['attacktime', 'attackmessage']

        for key, value in self.__dict__.items():
            if not key in ignore:
                ret[key] = value

        return ret

    def Deserialize(self, dic):
        for key, value in dic.items():
            self.__dict__[key] = value

    def Revert(self, messageid):
        if (len(self.history) == 0): return None

        ret = self.history[-1]
        if (ret['messageid'] == messageid):
            self.history.pop(-1)
            self.boss = ret['bosscount']
            return ret
        return None

    def dayfinish(self):
        return self.SortieCount() == MAX_SORITE

    async def Gacha(self, message):
        self.gacha += 1
        result = []
        box = gacha.GetBoxData()
        staremoji = ['', u"\U0001F499", u"\U0001F9E1", u"\U0001F49D"]
        rare = 0

        for i in range(10):
            princess = Gacha.LotteryPrincess(box, 1 if i < 9 else 2)
            result.append(princess)
            if (princess.star == 3): rare += 1

        if (self.gacha == 1):
            mes = '素敵な仲間が…　来るといいですねぇ～' 
            if (0 < rare and random.random() < 0.5):
                mes = 'かんぱ～い！ ' + u"\U0001F37B"

            post = await message.channel.send(mes)
            await asyncio.sleep(5)
            await post.delete()

            mes = ''
            for i, p in enumerate(result):
                mes += staremoji[p.star]
                if i == 4: mes += '\n'
            
            post = await message.channel.send(mes)
            await asyncio.sleep(5)
            await post.delete()
        
        await message.channel.send('\n'.join(['★%d %s' % (p.star, p.name) for p in result]))

        if (gacha.prize):
            resultprize : List[PrizeRate] = []
            for i in range(10):
                prize = Gacha.LotteryPrize(1 if i < 9 else 2)
                resultprize.append(prize)

            totalprize = PrizeRate(0, 0, 0, 0, 0)
            for pl in resultprize:
                totalprize.memorial += pl.memorial
                totalprize.stone += pl.stone
                totalprize.heart += pl.heart

            str = ' '.join([item.Name() for item in resultprize]) + '\n'
            str += 'メモピ%d個 ハート%d個 秘石%d個' % (totalprize.memorial, totalprize.heart, totalprize.stone)

            await message.channel.send(str)

    
class Cran():
    numbermarks = [
        "\N{DIGIT ZERO}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT SIX}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT SEVEN}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT EIGHT}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT NINE}\N{COMBINING ENCLOSING KEYCAP}",
    ]

    emojis = [
        u"\u2705",
        "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT SIX}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT SEVEN}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT EIGHT}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{DIGIT NINE}\N{COMBINING ENCLOSING KEYCAP}",
        u"\u274C",
    ]

    emojisoverkill = [
        u"\u2705",
        "\N{DIGIT ZERO}\N{COMBINING ENCLOSING KEYCAP}",
        u"\u274C",
    ]

    def __init__(self, channelid : int):
        self.members: Dict[int, CranMember] = {}
        self.bosscount = 0
        self.channelid = channelid
        self.lastmessage = None
        self.stampcheck :Dict[str, Any] = {}
        self.beforesortie = 0
        self.lap = {0 : 0.0}
        self.defeatlist = []

        self.guild = None
        self.inputchannel = None
        self.outputchannel = None

    def GetMember(self, author) -> CranMember:
        member = self.members.get(author.id)
        if (member is None):
            member = CranMember()
            self.members[author.id] = member
        member.name = author.display_name
        member.mention = author.mention
        return member

    def IsInput(self, channel_id):
        if self.inputchannel is None: return False
        return self.inputchannel.id == channel_id

    def FindMember(self, name) -> Optional[CranMember]:
        for member in self.members.values():
            if (member.name == name):
                return member
        return None

    def DeleteMember(self, name) -> Optional[CranMember]:
        for id, member in self.members.items():
            if (member.name == name):
                del self.members[id]
                return member
        return None

    def FullReset(self):
        self.bosscount = 0
        self.beforesortie = 0
        self.lap = {0 : 0.0}
        self.defeatlist.clear()
        self.Reset()

    def Reset(self):
        self.beforesortie = self.TotalSortie()
        self.lastmessage = None
        self.stampcheck = {}
        for member in self.members.values():
            member.Reset()

    def AddStamp(self, messageid):
        if (messageid in self.stampcheck):
            self.stampcheck['messageid'] += 1
        else:
            self.stampcheck['messageid'] = 1
        return self.stampcheck['messageid']

    def RemoveStamp(self, messageid):
        if (messageid in self.stampcheck):
            self.stampcheck['messageid'] -= 1
        else:
            self.stampcheck['messageid'] = 0
        return self.stampcheck['messageid']
    
    async def AddReaction(self, message, overkill):
        reactemojis = self.emojis if not overkill else self.emojisoverkill

        for emoji in reactemojis:
            await message.add_reaction(emoji)

    async def RemoveReaction(self, message, overkill, me):
        reactemojis = self.emojis if not overkill else self.emojisoverkill

        for emoji in reactemojis:
            await message.remove_reaction(emoji, me)

    async def SetNotice(self, member, message, bossstr):
        member.SetNotice(bossstr)

        if (member.notice is None):
            mark = self.numbermarks[0]
        else:
            mark = self.numbermarks[member.notice]

        await message.add_reaction(mark)

    async def MemberRefresh(self):
        mes = ''
        mlist = []
        deletemember = []

        for member in self.guild.members:
            if not member.bot:
                mlist.append(member.id)
                if self.members.get(member.id) is None:
                    self.GetMember(member)
                    mes += member.name + "を追加しました\n"

        for id, member in self.members.items():
            if (id not in mlist):
                deletemember.append(id)
                mes += member.name + "を削除しました\n"

        for id in deletemember:
            del self.members[id]

        if self.inputchannel is not None:
            await self.inputchannel.send(mes)

    def ScoreCalc(self, opt):
        try:
            score = int(opt)
            return CranScore.Calc(score)

        except ValueError:
            return None
    
    async def GachaAdd(self, opt, channel):
        gtype = opt[0]
        date = opt[1:20]
        name = opt[20:]
        mes = '%s [%s] [%s]' % (gtype, date, name)

        global GachaData
        GachaData.append(GachaSchedule(date, gtype, name))
        GlobalStrage.Save()

        await channel.send(mes)

    async def on_message(self, message):
        member = self.GetMember(message.author)
        mark = u"\u2757"

        self.inputchannel = message.channel
        
        if self.outputchannel is None:
            outchannel = [channel for channel in message.guild.channels if channel.name == outputchannel]
            if 0 < len(outchannel):
                self.outputchannel = client.get_channel(outchannel[0].id)

        if (message.content in CmdAttack):
            member.Attack(self)

            if (member.taskkill != 0):
                await message.add_reaction(mark)

            member.attackmessage = message
            await self.AddReaction(message, member.IsOverkill())
            return True
        
        if (message.content in CmdTaskkill):
            member.taskkill = message.id

            await message.add_reaction(mark)
            return True

        if (message.content == 'prevboss'):
            await self.ChangeBoss(message.channel, -1)
            return True

        if (message.content == 'nextboss'):
            await self.ChangeBoss(message.channel, 1)
            return True

        if (message.content == 'cranreset'):
            self.Reset()
            return True

        opt = Command(message.content, ['memo', 'メモ'])
        if (opt is not None):
            member.SetMemo(opt)
            return True

        opt = Command(message.content, ['notice', '通知'])
        if (opt is not None ):
            await self.SetNotice(member, message, opt)
            return False

        if (message.content == 'refresh'):
            await self.MemberRefresh()
            return True

        if (message.content == 'reset'):
            member.Reset()
            return True

        if (message.content == 'fullreset'):
            self.FullReset()
            return True

        opt = Command(message.content, 'history')
        if (opt is not None):
            if (opt == ''):
                await member.History(message)
            else:
                fmember = self.FindMember(opt)
                if fmember is not None:
                    await fmember.History(message)
                else:
                    await message.channel.send('メンバーがいません')
            return False

        opt = Command(message.content, 'bn')
        if (opt is not None):
            bindex = int(opt[:1]) - 1
            if (0 <= bindex and bindex < BOSSNUMBER):
                BossName[bindex] = opt[1:]
            return True

        if (message.content in ['gacha', 'ガチャ']):
            if (IsCranBattle()):
                return False
            else:
                await member.Gacha(message)
                return False
        
        if message.content in ['defeatlog']:
            await self.DefeatLog(message.channel)
            return False

        opt = Command(message.content, 'gachaadd')
        if (opt is not None):
            await self.GachaAdd(opt, message.channel)
            return False

        opt = Command(message.content, 'gachalist')
        if (opt is not None):
            await message.channel.send(Gacha.GachaScheduleData())
            return False

        if (message.content in ['gachasave']):
            gacha.GachaSave()
            return False

        if (message.content in ['gdata']):
            await message.channel.send(gacha.ToString())
            return False

        opt = Command(message.content, 'delete')
        if (opt is not None):
            result = self.DeleteMember(opt)
            if (result is not None):
                await message.channel.send('%s を消しました' % result.name)
                return True
            else:
                await message.channel.send('メンバーがいません')
                return False
        
        opt = Command(message.content, 'score')
        if (opt is not None):
            result = self.ScoreCalc(opt)
            if (result is not None):
                await message.channel.send('%d-%d %s (残りHP %s %%)' % 
                (result.lap, result.bossindex + 1, BossName[result.bossindex], result.hprate))
                return True
            else:
                await message.channel.send('計算できませんでした')
                return False

        return False

    async def on_raw_message_delete(self, payload):
        if payload.cached_message is None:
            return False

        member = self.members.get(payload.cached_message.author.id)
        if member is None: return False

        if member.Revert(payload.message_id) is not None:
            member.Cancel(self)
            return True

        if member.taskkill == payload.message_id:
            member.taskkill = 0
            return True

        return False

    def emojiindex(self, emojistr):
        for idx, emoji in enumerate(self.emojis):
            if emoji == emojistr:
                return idx
        for idx, emoji in enumerate(self.emojisoverkill):
            if emoji == emojistr:
                return idx
        return None

    def CreateNotice(self, boss):
        boss = boss + 1
        notice = []
        for member in self.members.values():
            if (member.notice == boss):
                notice.append(member.mention)

        if (len(notice) == 0):       
            return None
        else:
            return ' '.join(notice)

    def AddDefeatTime(self, count):
        l = len(self.defeatlist)

        if l < count:
            for _i in range(count - l):
                self.defeatlist.append('2000/01/01 00:00:00')
        
        self.defeatlist[count - 1] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    async def ChangeBoss(self, channel, count):
        self.bosscount += count
        if (self.bosscount < 0):
            self.bosscount = 0
        await channel.send('次のボスは %s です' % (BossName[self.BossIndex()]) )

        if (0 < count):
            self.AddDefeatTime(self.bosscount)

            if (self.bosscount % BOSSNUMBER == 0):
                self.lap[self.bosscount // BOSSNUMBER] = self.TotalSortie()

            notice = self.CreateNotice(self.BossIndex())
            if (notice is not None):
               await channel.send('%s %s がやってきました' % (notice, BossName[self.BossIndex()]))

    async def DefeatLog(self, channel):
        text = ''
        for n in self.defeatlist:
            text += n + '\n'

        with StringIO(text) as bs:
            await channel.send(file=discord.File(bs, 'defeatlog.txt'))

    async def on_reaction_add(self, reaction, user):
        idx = self.emojiindex(reaction.emoji)
        Outlog(ERRFILE, "on_reaction_add %s [%d]" % 
            (reaction.message.author.display_name, reaction.message.author.id ) )

        if idx is None:
            return False

        message = reaction.message
        v = self.AddStamp(message.id)
        if (v != 1):
            Outlog(ERRFILE, "self.AddStamp" + " " + v)
            return False

        member = self.GetMember(message.author)
        if (member.MessageChcck(message.id)):
            Outlog(ERRFILE, "member.MessageChcck is none")
            return False

        overkill = member.IsOverkill()

        if (idx == 0):
            member.Finish(self, message.id)
            member.notice = None
        
        if (1 <= idx and idx <= 8):
            boss = member.boss
            if (overkill):
                member.Finish(self, message.id, True)
            else:
                member.Overkill(self, (idx + 1) * 10, message.id)

            member.notice = None

            if (self.bosscount == boss):
                await self.ChangeBoss(message.channel, 1)
        
        if (idx == 9):
            member.Cancel(self)

        await self.RemoveReaction(message, overkill, message.guild.me)

        return True

    async def on_raw_reaction_add(self, payload):
        member = self.members.get(payload.user_id)
        if member is None:
            return False

        if self.inputchannel is None or self.inputchannel.id != payload.channel_id:
            return False

        if member.attackmessage is None or member.attackmessage.id != payload.message_id:
            return False

        Outlog(ERRFILE, "on_raw_reaction_add [%d]" % (payload.user_id))

        idx = self.emojiindex(payload.emoji.name)
        if idx is None:
            return False

        v = self.AddStamp(payload.message_id)
        if (v != 1):
            Outlog(ERRFILE, "self.AddStamp" + " " + v)
            return False

        if (member.MessageChcck(payload.message_id)):
            Outlog(ERRFILE, "member.MessageChcck is none")
            return False

        overkill = member.IsOverkill()

        if (idx == 0):
            member.Finish(self, payload.message_id)
            member.notice = None
        
        if (1 <= idx and idx <= 8):
            boss = member.boss
            if (overkill):
                member.Finish(self, payload.message_id, True)
            else:
                member.Overkill(self, (idx + 1) * 10, payload.message_id)

            member.notice = None

            if (self.bosscount == boss):
                if self.inputchannel is not None:
                    await self.ChangeBoss(self.inputchannel, 1)
        
        if (idx == 9):
            member.Cancel(self)

        message = member.attackmessage
        await self.RemoveReaction(message, overkill, message.guild.me)
        return True

    async def on_reaction_remove(self, reaction, user):
        idx = self.emojiindex(reaction.emoji)
        Outlog(ERRFILE, "on_reaction_remove " + reaction.message.author.display_name)

        if (idx is None):
            return False

        message = reaction.message
        member = self.GetMember(message.author)

        v = self.RemoveStamp(message.id)
        if (v != 0):
            Outlog(ERRFILE, message.author.display_name + " " + v)
            return False

        if (message.content in CmdAttack):
            if(idx == 9):
                member.Attack(self, False)
                await self.AddReaction(message, member.IsOverkill())
                return True

            data = member.Revert(message.id)
            if (data is not None):
                member.Attack(self, False)
                if (data['defeat']):
                    if (data['bosscount'] + 1 == self.bosscount):
                        await self.ChangeBoss(reaction.message.channel, -1)
                    await reaction.message.channel.send('ボスが食い違う場合は手動で調整してください\n「prevboss」で前のボス、「nextboss」で次のボスに設定します')
                
                await self.AddReaction(message, member.IsOverkill())

                return True
            else:
                await reaction.message.channel.send('巻き戻しに失敗しました')

        return False

    async def on_raw_reaction_remove(self, payload):
        member = self.members.get(payload.user_id)
        if member is None:
            return False

        if self.inputchannel is None or self.inputchannel.id != payload.channel_id:
            return False

        Outlog(ERRFILE, "on_raw_reaction_remove [%d]" % (payload.user_id))

        idx = self.emojiindex(payload.emoji.name)
        if idx is None:
            return False

        v = self.RemoveStamp(payload.message_id)
        if (v != 0):
            return False

        if (member.attackmessage is not None and member.attackmessage.id == payload.message_id):
            if(idx == 9):
                member.Attack(self, False)
                await self.AddReaction(member.attackmessage, member.IsOverkill())
                return True

            data = member.Revert(payload.message_id)
            if (data is not None):
                member.Attack(self, False)
                if (data['defeat']):
                    if (data['bosscount'] + 1 == self.bosscount):
                        await self.ChangeBoss(self.inputchannel, -1)
                    await self.inputchannel.send('ボスが食い違う場合は手動で調整してください\n「prevboss」で前のボス、「nextboss」で次のボスに設定します')
                
                await self.AddReaction(member.attackmessage, member.IsOverkill())

                return True
            else:
                await self.inputchannel.send('巻き戻しに失敗しました')

        return False
                        
    def SortieCount(self):
        count = 0
        for member in self.members.values():
            count += member.SortieCount()
        return count

    def TotalSortie(self):
        count = self.SortieCount() + 0.0
        for member in self.members.values():
            if member.IsOverkill():
                count += 0.5
        return count + self.beforesortie

    def GetLevelUpLap(self, lap):
        for lv in reversed(LevelUpLap):
            if lv - 1 <= lap:
                return lv - 1
        return 0

    def LapAverage(self):
        nowlap = self.bosscount // BOSSNUMBER

        if nowlap == 0 or nowlap not in self.lap:
            return 0

        lvup = self.GetLevelUpLap(nowlap)

        for i in reversed(range(1, 4)):
            baselap = nowlap - i
            if lvup <= baselap and baselap in self.lap:
                return (self.lap[nowlap] - self.lap[baselap] ) / i

        return 0

    def BossIndex(self):
        return self.bosscount % BOSSNUMBER
    
    def BossLevel(self):
        level = 1
        lap = self.bosscount // BOSSNUMBER
        for lvlap in LevelUpLap:
            if lap < lvlap :
                return level
            level += 1
        return level

    def NextLvUpLap(self):
        levelindex = self.BossLevel() - 1

        if len(LevelUpLap) <= levelindex: return 0
        return (LevelUpLap[levelindex] - self.bosscount / 5 - 1)

    def Status(self):
        s = ''
        s += '現在 %d-%d %s\n' % (self.bosscount // BOSSNUMBER + 1, self.BossIndex() + 1, BossName[self.BossIndex()])

        attackcount = 0
        count : List[List[CranMember]] = [[], [], [], []]
        overkill = ''
        okcount = 0
        attack = ''

        for member in self.members.values():
            count[member.SortieCount()].append(member)
            attackcount += member.SortieCount()
            if (member.IsOverkill()):
                overkill += '%s %s:%d秒' % (member.name, BossName[member.Overboss() % BOSSNUMBER], member.Overtime())
                if (member.Memo() != ''):
                    overkill += ' %s' % (member.Memo())
                overkill += '\n'
                okcount += 1
            if (member.attack):
                if (attack != ''):
                    attack += ' '
                attack += '%s' % (member.name)

        if (attack != ''):
            s += '攻撃中\n' + attack + '\n'

        if (overkill != ''):
            s += '持ち越し %d人\n' % (okcount) + overkill + '\n'

        restattack = len(self.members) * MAX_SORITE - attackcount
        lap = self.LapAverage()
        restlap = ((restattack - okcount * 0.5) / lap) if 0 < lap else 0 

        nextlap = self.NextLvUpLap()
        nextstr = ''
        if 0 < nextlap and 0 < lap:
            nextstr = ' / %d段階目まで%.1f凸' % (self.BossLevel() + 1, nextlap * lap)

        s += '総攻撃数 %d回 (残り %d回 約%.1f周%s)\n' % (attackcount, restattack, restlap, nextstr)

        for i, c in enumerate(count):
            s += '%d回目 %d人\n' % (i, len(c))
            first = True
            for member in c:
                if (first):
                    first = False
                else:
                    s += '  '
                s += member.name
                if (member.IsOverkill()):
                    s += "[o]"
                if (member.taskkill != 0):
                    s += "[tk]"
            s += '\n'
        
        return s

    @staticmethod
    def Save(cran, cranid):
        dic = {
            'members': {},
            'bosscount' : cran.bosscount,
            'channelid' : cran.channelid,
            'beforesortie' : cran.beforesortie,
            'lap' : cran.lap,
            'defeatlist' : cran.defeatlist,
        }

        for mid, member in cran.members.items():
            dic['members'][mid] = member.Serialize()

        with open('crandata/%d.json' % (cranid) , 'w') as a:
            json.dump(dic, a , indent=4)

    @staticmethod
    def Load(cranid):
        with open('crandata/%d.json' % (cranid)) as a:
            mdic =  json.load(a)

            cran = Cran(mdic['channelid'])
            cran.bosscount = mdic['bosscount']

            if ('beforesortie' in mdic):
                cran.beforesortie = mdic['beforesortie']
            
            if ('defeatlist' in mdic):
                cran.defeatlist = mdic['defeatlist']

            if ('lap' in mdic):
                for key, value  in mdic['lap'].items():
                    cran.lap[int(float(key))] = value

            for mid, dicmember in mdic['members'].items():
                member = CranMember()
                member.Deserialize(dicmember)
                cran.members[int(mid)] = member

            return cran

# 接続に必要なオブジェクトを生成
client = discord.Client()

cranhash = {}

# ギルドデータ読み込み
files = glob.glob("./crandata/*.json")

for file in files:
    cranid = int (os.path.splitext(os.path.basename(file))[0])
    if cranid != 0:
        cran = Cran.Load(cranid)
        cranhash[cranid] = cran

def GetCran(guild, message) -> Cran:
    global cranhash
    g = cranhash.get(guild.id)

    if (g is None):
        g = Cran(message.channel.id)
        cranhash[guild.id] = g

    if g.guild is None:
        g.guild = guild

    return g

@tasks.loop(seconds=60)
async def loop():
    # 現在の時刻
    now = datetime.datetime.now()
    nowdate = now.strftime('%m/%d')
    nowtime = now.strftime('%H:%M')

    if nowtime == '05:00':
        for cran in cranhash.values():
            message = 'おはようございます\nメンバーの情報をリセットしました'
            resetflag = True if cran.TotalSortie() == 0 else False

            if (nowdate == BATTLEPRESTART):
                message = 'おはようございます\n明日よりクランバトルです。状況報告に名前が出ていない人は、今日中に「凸」と発言してください。'
                cran.FullReset()
                resetflag = True

            if (nowdate == BATTLESTART):
                message = 'おはようございます\nいよいよクランバトルの開始です。頑張りましょう。'
                cran.FullReset()
                resetflag = True

            if (nowdate == BATTLEEND):
                message = 'おはようございます\n今日がクランバトル最終日です。24時が終了時刻ですので早めに攻撃を終わらせましょう。'
                resetflag = True

            cran.Reset()
            if resetflag:
                if cran.inputchannel is not None:
                    await cran.inputchannel.send(message)
                    await Output(cran, cran.Status())
            else:
                cran.lastmessage = None

    if nowtime == '23:59':
        for cran in cranhash.values():
            if (nowdate == BATTLEEND):
                if cran.inputchannel is not None:
                    message = 'クランバトル終了です。お疲れさまでした。'
                    await cran.inputchannel.send(message)
    
    shtime = now + datetime.timedelta(minutes = -15)
    for cran in cranhash.values():
        for member in cran.members.values():
            if (member.attacktime is not None and member.attacktime < shtime):
                member.attacktime = None

                if cran.inputchannel is not None:
                    message = '%s 凸結果の報告をお願いします' % member.mention
                    await cran.inputchannel.send(message)


def IsCranBattle():
    return False


# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')
    Outlog(ERRFILE, "login.")

async def VolatilityMessage(message, mes, time):
    log = await message.channel.send(mes)
    await asyncio.sleep(time)
    await log.delete()

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    if message.channel.name != inputchannel:
        return

    cran = GetCran(message.guild, message)
    result = await cran.on_message(message)

    if (result):
        cran.Save(cran, message.guild.id)
        await Output(cran, cran.Status())

@client.event
async def on_raw_message_delete(payload):
    cran = cranhash.get(payload.guild_id)

    if cran is not None and cran.IsInput(payload.channel_id):

        result = await cran.on_raw_message_delete(payload)
        if result:
            cran.Save(cran, payload.guild_id)
            await Output(cran, cran.Status())

@client.event
async def on_raw_reaction_add(payload):
    cran = cranhash.get(payload.guild_id)

    if cran is not None:
        result = await cran.on_raw_reaction_add(payload)
        if result:
            cran.Save(cran, payload.guild_id)
            await Output(cran, cran.Status())

@client.event
async def on_raw_reaction_remove(payload):

    cran = cranhash.get(payload.guild_id)

    if cran is not None and cran.IsInput(payload.channel_id):

        result = await cran.on_raw_reaction_remove(payload)
        if result:
            cran.Save(cran, payload.guild_id)
            await Output(cran, cran.Status())

@client.event
async def on_member_remove(member):
    cran = cranhash.get(member.guild.id)
    if (cran is None): return

    member = cran.members.get(member.id)
    if (member is not None):
        del cran.members[id]
        cran.Save(cran, member.guild.id)
        await Output(cran, cran.Status())

@client.event
async def on_guild_remove(guild):
    global cranhash

    if guild.id in cranhash:
        del cranhash[guild.id]
        os.remove('crandata/%d.json' % (guild.id))

async def Output(cran, message):
    if cran.outputchannel is not None:
        if (cran.lastmessage is not None):
            await cran.lastmessage.delete()
            cran.lastmessage = None

        if cran.outputchannel is not None:
            cran.lastmessage = await cran.outputchannel.send(message)

def Outlog(filename, data):
    datetime_format = datetime.datetime.now()
    datestr = datetime_format.strftime("%Y/%m/%d %H:%M:%S")  # 2017/11/12 09:55:28
    print(datestr + " " + data, file=codecs.open(filename, 'a', 'utf-8'))

GlobalStrage.Load()

#ループ処理実行
loop.start()

# Botの起動とDiscordサーバーへの接続
client.run(tokenkeycode.TOKEN)

