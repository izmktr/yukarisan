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

LevelUpLap = [4, 11, 31, 41]
BossHpData = [
    [   [600, 1.2], [800, 1.2], [1000, 1.3], [1200, 1.4], [1500, 1.5] ],
    [   [600, 1.6], [800, 1.6], [1000, 1.8], [1200, 1.9], [1500, 2.0] ],
    [   [1200, 2.0], [1400, 2.0], [1700, 2.4], [1900, 2.4], [2200, 2.6] ],
    [   [1800, 3.5], [1900, 3.5], [2300, 3.7], [2300, 3.8], [2700, 4.0] ],
    [   [8500, 3.5], [9000, 3.5], [9500, 3.7], [10000, 3.8], [11000, 4.0] ],
]

GachaLotData = [
    [0.7, 0.0, 1.8, 18, 100], # 通常
    [0.7, 0.0, 1.8, 18, 100], # 限定
    [0.7, 0.0, 1.8, 18, 100], # プライズ
    [1.4, 0.0, 3.6, 18, 100], # 通常(2倍)
    [0.7, 0.9, 3.4, 18, 100], # プリフェス
]

ERRFILE = 'error.log'
SETTINGFILE = 'setting.json'
PARTYFILE = 'party.json'

#---設定ここまで---

BossLapScore = []
for l in BossHpData:
    lapscore = 0
    for i in l:
        lapscore += i[0] * i[1]
        i.append(i[0] * i[1])
    BossLapScore.append(lapscore)

GachaData = []

from os.path import expanduser
from re import match, split
from types import MemberDescriptorType
import tokenkeycode

import asyncio
import discord
from discord.ext import tasks
import datetime 
import json
import glob
import os
import re
import codecs
import random
from typing import List, Dict, Any, Optional, Tuple
from io import StringIO
from typing import Sequence, TypeVar
from functools import cmp_to_key

#from PIL import Image
#import numpy as np

T = TypeVar('T') 

BOSSNUMBER = len(BossName)

def sign(n : int):
    if n < 0 : return -1
    if 0 < n : return 1
    return 0

class GachaRate():
    def __init__(self, rate, star, namelist):
        self.rate : float = rate
        self.star : int = star
        self.namelist : List[str] = namelist

class PrizeRate():
    def __init__(self, rate, star, memorial, stone, heart):
        self.rate : float = rate
        self.star : int = star
        self.memorial : int = memorial
        self.stone : int = stone
        self.heart : int = heart
    
    def Name(self):
        star = 7 - self.star 
        if star <= 3:
            return '[%d等]' % (star)
        return '%d等' % (star)

class Princess():
    def __init__(self, name, star):
        self.name = name
        self.star = star
    
    def starstr(self):
        if 3 <= self.star:
            return "[★%d]" % self.star
        return "★%d" % self.star

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
        global BATTLEPRESTART
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
                start = datetime.datetime.strptime(BATTLESTART, '%m/%d')
                BATTLEPRESTART = (start + datetime.timedelta(days = -1)).strftime('%m/%d')

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
    pname =  ['ユイ(プリンセス)', 'コッコロ(プリンセス)', 'ペコリーヌ(プリンセス)', 'クリスティーナ', 'ムイミ', 'ネネカ']
    s3name = ['マコト','キョウカ','トモ','ルナ','カスミ','ジュン','アリサ','アン','クウカ(オーエド)',
            'ニノン(オーエド)','ミミ(ハロウィン)','ルカ','クロエ','イリヤ','アンナ','グレア','カヤ',
            'イリヤ(クリスマス)','カスミ(マジカル)','ノゾミ','マホ','シズル','サレン','ジータ','ニノン',
            'リノ','アキノ','モニカ','イオ','ハツネ','アオイ(編入生)','ユニ','チエル','リン(レンジャー)',
            'マヒル(レンジャー)','リノ(ワンダー)','イノリ', 'ナナカ(サマー)']
    s2name = ['カオリ','ナナカ','エリコ','シオリ','ミミ','タマキ','マツリ','スズナ','ミヤコ','クウカ',
            'アカリ','ミツキ','ツムギ','ミサト','アヤネ','シノブ','チカ','ミフユ','リン','ユキ','マヒル']
    s1name = ['レイ','ヨリ','ヒヨリ','リマ','ユカリ','クルミ','ミソギ','スズメ','アユミ','アオイ','ミサキ']

    limited = ['ユイ(ニューイヤー)','ヒヨリ(ニューイヤー)','キャル(ニューイヤー)','コッコロ(ニューイヤー)',
            'シズル(バレンタイン)','ペコリーヌ(サマー)','スズメ(サマー)','タマキ(サマー)','キャル(サマー)',
            'スズナ(サマー)','サレン(サマー)','マホ(サマー)','マコト(サマー)','ルカ(サマー)',
            'シノブ(ハロウィン)','キョウカ(ハロウィン)','チカ(クリスマス)','アヤネ(クリスマス)',
            'クリスティーナ(クリスマス)','エミリア','レム','ウヅキ(デレマス)','リン(デレマス)',]
    event = ['レイ(ニューイヤー)','スズメ(ニューイヤー)','エリコ(バレンタイン)','コッコロ(サマー)',
            'ミフユ(サマー)','イオ(サマー)','カオリ(サマー)','アンナ(サマー)','ミヤコ(ハロウィン)',
            'ミソギ(ハロウィン)','クルミ(クリスマス)','ノゾミ(クリスマス)','ラム','ミオ(デレマス)',
            'アユミ(ワンダー)', 'キャル','ペコリーヌ','コッコロ','ユイ']


    def __init__(self):
        self.gachabox : List[GachaRate] = []
        self.limitdate = '2000/01/01 00:00:00'
        self.gachatype = '3'
        self.prize = False

    def GachaSave(self):
        global GachaData

        GachaData = []
        for n in self.s3name:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', '3', n))

        for n in self.s2name:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', '2', n))

        for n in self.s1name:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', '1', n))

        for n in self.pname:
            GachaData.append(GachaSchedule('2000/01/01 00:00:00', 'f', n))

        GachaData.append(GachaSchedule('2020/06/24 12:00:00', 'p', 'クリスティーナ(クリスマス)'))
        GachaData.append(GachaSchedule('2020/06/30 12:00:00', 'f', 'ユイ(プリンセス)'))

        GlobalStrage.Save()

    @staticmethod
    def typetoindex(c) -> int:
        if (c == 'd'): return 0
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

    def FindPrincess(self, name):
        if len(self.gachabox) == 0:
            self.GetBoxData()
        
        if name in self.limited: return 'l'
        if name in self.gachabox[0].namelist: return self.gachatype
        if name in self.gachabox[1].namelist: return 'f'
        if name in self.gachabox[2].namelist: return '3'
        if name in self.gachabox[3].namelist: return '2'
        if name in self.gachabox[4].namelist: return '1'

        return '0'

    @staticmethod
    def AppendList(namelist, name):
        if type(name) is list:
            for n in name:
                if n not in namelist:
                   namelist.append(n)
        else:
            if name not in namelist:
                namelist.append(name)

    def BoxReset(self):
        self.gachabox = []
        self.limitdate = '2000/01/01 00:00:00'

    def GetBoxData(self) -> List[GachaRate]:
        datetime_format = datetime.datetime.now()
        datestr = datetime_format.strftime("%Y/%m/%d %H:%M:%S")  # 2017/11/12 09:55:28

        if self.limitdate is None:
            if GachaData[-1].startdate <= datestr:
                return self.gachabox
        elif datestr < self.limitdate:
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
                self.AppendList(self.gachabox[n].namelist, m.name)
            else:
                self.AppendList(self.limited, m.name)

        self.PickUpDelete(pickup.name)
        self.AppendList(self.gachabox[0].namelist, pickup.name)
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
        message += '%s %s\n' % (self.GachaType(self.gachatype), GachaData[-1].startdate)

        for rate in self.gachabox:
            unitrate = 0.0 if len(rate.namelist) <= 0 else rate.rate / len(rate.namelist)
            message += '%0.3f(%0.3f) %d %s len:%d\n' % (rate.rate, unitrate, rate.star, rate.namelist[-1], len(rate.namelist) )

        return message

    @staticmethod
    def GachaType(g):
        if g == '1' : return '恒常星1'
        if g == '2' : return '恒常星2'
        if g == '3' : return '恒常星3'
        if g == 'l' : return '限定'
        if g == 'd' : return '2倍'
        if g == 'p' : return 'プライズ'
        if g == 'f' : return 'プリフェス'
        return 'Unknown'

    @staticmethod
    def GachaScheduleData():
        message = ''
        num = 0
        for m in reversed(GachaData):
            if 9 <= num or m.startdate <= '2000/01/01 00:00:00':
                break
            message +=  '%d: %s [%s] [%s]\n' % (num + 1, m.startdate, Gacha.GachaType(m.gachatype), Gacha.NameListToString(m.name) )
            num += 1
        
        return message
       
    @staticmethod
    def Lottery(box : List[T], leaststar = 1) -> T:
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

class ScoreCalcResult:
    def __init__(self, lap, level, bindex, hprate, modscore):
        self.lap = lap
        self.level = level
        self.bossindex = bindex
        self.hprate = hprate
        self.modscore = modscore

class ClanScore:
    @staticmethod
    def Calc(score) -> Optional[ScoreCalcResult]:
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
                return ScoreCalcResult(lap, level, bindex, hprate,  modscore)
            totalscore += nowbossscore
            bindex += 1

        return None

#ユカリさん相談

class StringChopper:
    def __init__(self):
        self.initialdic :Dict[str, List[str]] = {}
    
    def Register(self, name):
        length = len(name)
        if length == 0: return

        page = self.initialdic.get(name[0])
        if page is None:
            self.initialdic[name[0]] = [name]
            return

        pagelength = len(page)
        for i in range(0, pagelength):
            if name == page[i]: return
            if name < page[i]:
                page.insert(i, name)
                return
        page.append(name)
    
    def Print(self):
        for value in self.initialdic.values():
            for name in value:
                print(name)
    
    def Serialize(self) -> List[str]:
        result = []
        for value in self.initialdic.values():
            for name in value:
                result.append(name)

        return result
    
    def Deserialize(self, datalist):
        for data in datalist:
            self.Register(data)

    def Chopper(self, namelist : str) -> Optional[List[str]]:
        if len(namelist) == 0: return []
        tmpname = namelist

        page = None
        while 0 < len(tmpname):
            page = self.initialdic.get(tmpname[0])
            if page is not None:
                break
            tmpname = tmpname[1:]
        if len(tmpname) == 0: return None

        for s in page:
            if tmpname.startswith(s):
                result = [s]
                a = self.Chopper(tmpname[len(s):])
                if a is None: continue
                result.extend(a)
                return result

        return None
    
class PrincessIndex:
    def __init__(self):
        self.name2index :Dict[str, int] = {}
        self.index2name :Dict[int, str] = {}
        self.charactorChopper = StringChopper()

    def Register(self, index :int, name :str, alias: bool):
        if name in self.name2index:
            print('%s is concrift.' % name)
            return

        self.name2index[name] = index

        if not alias: self.index2name[index] = name

    def GetIndex(self, name : str) -> int:
        n = self.name2index.get(name)
        return n if n is not None else 0

    def GetName(self, index : int) -> str:
        name = self.index2name.get(index)
        return name if name is not None else ''

    def Convert2Name(self, namearray) -> List[str]:
        return [self.index2name[n] for n in namearray]

    def Convert2Index(self, indexarray) -> List[int]:
        return [self.GetIndex(n) for n in indexarray]

    def Chopper(self, name : str) -> Optional[List[int]]:
        result = self.charactorChopper.Chopper(name)
        if result is not None:
            return self.Convert2Index(result)

        return None

    def Load(self):
        with open('princess.txt') as f:
            for s_line in f:
                namearray = s_line.split()
                if len(namearray) < 2: continue
                index = int(namearray[0])
                for i in range(1, len(namearray)):
                    self.Register(index, namearray[i], i != 1)
                    self.charactorChopper.Register(namearray[i])

princessIndex = PrincessIndex()
princessIndex.Load()


class PartyInfomation:
    def __init__(self, boss, party, memo, share, userid):
        self.boss: int = boss
        self.party = set(party)
        self.memo :str = memo
        self.share :int = share  # 0:global, 1:private
        self.userid = userid
        self.index = 0
        self.score = 0

    def PartyMatch(self, party: set):
        return len(self.party & party)

    def Viewable(self, userid):
        if self.share == 0 : return True
        if self.share == 1 and userid == self.userid : return True
        return False
    
    def PrincessName(self):
        return '/'.join(princessIndex.Convert2Name(self.party))

    def InfoOneLine(self):
        return '%d%03d %s' % (self.boss, self.index, self.PrincessName())

    def InfoOneLineRecomend(self, unused: set):
        n = self.party - unused
        if 0 < len(n):
            pname = '/'.join(princessIndex.Convert2Name(self.party - n))
            support = '/'.join(princessIndex.Convert2Name(n))
            return '%d%03d %s/[%s]' % (self.boss, self.index, pname, support)
        else:
            return self.InfoOneLine()

    def Infomation(self):
        return '%d%03d %s\n%s' % (self.boss, self.index, self.PrincessName(), self.memo)

    def BossInfo(self):
        return '%d段階目 %s' % (self.boss // 10, BossName[self.boss % 10 - 1])

    def Serialize(self):
        serial = {
            'boss': self.boss,
            'party': list(self.party),
            'memo' : self.memo,
            'share' : self.share,
            'userid' : self.userid,
            'index' : self.index,
            'score' : self.score,
        }

        return serial

    @staticmethod
    def Deserialize(list):
        des = PartyInfomation(0, [], '', 0, 0)
        for key, value in list.items():
            if key == 'party':
                des.party = set(value)
            else:
                des.__dict__[key] = value
        return des


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

class ClanMember():

    def __init__(self):
        self.attack = False
        self.reportlimit = None
        self.name = ''
        self.taskkill = 0
        self.history : List[Dict[str, Any]] = []
        self.boss = 0
        self.notice = None
        self.mention = ''
        self.gacha = 0
        self.route = []
        self.attackmessage: Optional[discord.Message] = None
        self.lastactive = datetime.datetime.now() + datetime.timedelta(days = -1)

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


    def Attack(self, clan, renewal = True):
        self.attack = True
        self.reportlimit = datetime.datetime.now() + datetime.timedelta(minutes = 30)

        if (renewal):
            self.boss = clan.bosscount

    def DecoName(self, opt : str) -> str:
        s = ''
        for c in opt:
            if c == 'n': s += self.name
            elif c == 's': 
                s += '%d凸' % self.SortieCount()
            elif c == 'S': 
                s += '[%d凸]' % self.SortieCount()
            elif c == 't': 
                if self.taskkill: s += 'tk'
            elif c == 'T': 
                if self.taskkill: s += '[tk]'
            elif c == 'o':
                if self.IsOverkill(): s += 'o%d' % (self.Overtime() // 10)
            elif c == 'O':
                if self.IsOverkill(): s += '[o%d]' % (self.Overtime() // 10)
            else: s += c

        return s

    def SortieCount(self):
        count = 0
        for h in self.history:
            if (h['overtime'] == 0):
                 count += 1
        if (MAX_SORITE <= count):
            return MAX_SORITE
        return count

    def Finish(self, clan, messageid, defeat = False):
        self.attack = False
        self.reportlimit = None
        self.CreateHistory(messageid, self.boss, 0, defeat)
    
    def Cancel(self, clan):
        self.attack = False
        self.reportlimit = None

    def Overkill(self, clan, overtime, messageid):
        self.attack = False
        self.reportlimit = None
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
        self.reportlimit = None
        self.taskkill = 0
        self.history = []
        self.notice = None
        self.gacha = 0

    def OverKillMessage(self):
        if not self.IsOverkill():
            return ''

        overkill = '%s %s:%d秒' % (self.DecoName('nS'), BossName[self.Overboss() % BOSSNUMBER], self.Overtime())
        if self.Memo() != '':
            overkill += ' %s' % (self.Memo())
        return overkill

    def ChangeableTime(self, time):
        if time == 0: return True

        l = len(self.history)
        if 1 <= l and 0 < self.history[-1]['overtime']: return True
        if l == 1: return True
        if 2 <= l and self.history[-2]['overtime'] == 0: return True

        return False

    def ChangeOvertime(self, time):
        if len(self.history) == 0:
            return '前の凸がありません'
        
        if self.ChangeableTime(time):
            self.history[-1]['overtime'] = time
        else:
            return '前の凸が持ち越しです'
        return None

    def AttackName(self):
        s = self.name
        if (self.IsOverkill()):
            s += "[o%d]" % (self.Overtime() // 10)
        if (self.taskkill != 0):
            s += "[tk]"
        return s

    def History(self):
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
        return str

    def SetNotice(self, bossstr):
        try:
            boss = int(bossstr)
            if (boss <= 0 or BOSSNUMBER < boss):
                self.notice = None
            else:
                self.notice = boss
        except ValueError:
            pass

    def GetUnfinishRoute(self):
        if self.DayFinish() or len(self.route) == 0: return []

        route = set(self.route)
        attack = set()

        before = {'defeat' : False}
        for h in self.history:
            if before['defeat']:
                time = before['overtime']
            else:
                time = 110 - h['overtime']

            if 50 <= time:
                attack.add(h['bosscount'] % BOSSNUMBER + 1)
            before = h
        
        return list(route - attack)

    def Serialize(self):
        ret = {}
        selializemember = ['attack', 'name', 'taskkill', 'history', 'boss', 'notice', 'gacha', 'route']

        for key, value in self.__dict__.items():
            if key in selializemember:
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

    def DayFinish(self):
        return self.SortieCount() == MAX_SORITE
    
    def UpdateActive(self):
        self.lastactive = datetime.datetime.now()

    async def Gacha(self, channel):
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

            post = await channel.send(mes)
            await asyncio.sleep(5)
            await post.delete()

            mes = ''
            for i, p in enumerate(result):
                mes += staremoji[p.star]
                if i == 4: mes += '\n'
            
            post = await channel.send(mes)
            await asyncio.sleep(5)
            await post.delete()

        mes = '\n'.join(['%s %s' % (p.starstr(), p.name) for p in result])

        if gacha.prize:
            resultprize : List[PrizeRate] = []
            for i in range(10):
                prize = Gacha.LotteryPrize(1 if i < 9 else 2)
                resultprize.append(prize)

            totalprize = PrizeRate(0, 0, 0, 0, 0)
            for pl in resultprize:
                totalprize.memorial += pl.memorial
                totalprize.stone += pl.stone
                totalprize.heart += pl.heart

            mes += '\n' + ' '.join([item.Name() for item in resultprize]) + '\n'
            mes += 'メモピ%d個 ハート%d個 秘石%d個' % (totalprize.memorial, totalprize.heart, totalprize.stone)

        await channel.send(mes)

    async def Gacha10000(self, channel):
        dic = {}
        box = gacha.GetBoxData()
        for _i in range(10000):
            princess = Gacha.LotteryPrincess(box, 1)

            if 3 <=princess.star:
                name = princess.name if '!' in princess.name else 'すり抜け星3'

                if name in dic:
                    dic[name] += 1
                else:
                    dic[name] = 1
        
        mes = ''
        for name, count in dic.items():
            mes += '%s:%d\n' % (name, count)
        
        await channel.send(mes)

class DamageControlMember:

    def __init__(self, member : ClanMember, damage : int, message : str = '') -> None:
        self.member : ClanMember = member
        self.damage = damage
        self.status = 0
        self.message = message

class DamageControl():

    def __init__(self, clanmembers : Dict[int, ClanMember]):
        self.active = False
        self.lastmessage = None
        self.channel = None
        self.remainhp = 0
        self.bossindex = 0
        self.members : Dict[ClanMember, DamageControlMember] = {}
        self.outputlock = 0
        self.clanmembers : Dict[int, ClanMember]= clanmembers

    def SetChannel(self, channel):
        self.channel = channel

    def RemainHp(self, bossindex: int, hp : int):
        self.active = True
        self.bossindex = bossindex
        self.remainhp = hp

    async def TryDisplay(self):
        if 0 < len(self.members):
             await self.SendResult()

    def Damage(self, member : ClanMember, damage : int, message : str = ''):
        self.members[member] = DamageControlMember(member, damage, message)

    def MemberSweep(self):
        if len([m for m in self.members.values() if m.status == 0]) == 0:
            self.members.clear()

    async def Remove(self, member : ClanMember):
        if not self.active: return

        resultflag = 0 < len(self.members)
        if member in self.members:
            del self.members[member]
            self.MemberSweep()

        if resultflag:
            await self.SendResult()

    async def Injure(self, member : ClanMember):
        if not self.active: return
        
        resultflag = 0 < len(self.members)

        if member in self.members:
            m = self.members[member]
            self.remainhp -= m.damage
            if self.remainhp < 0 : self.remainhp = 0
            
            m.damage = 0
            m.status = 1

            self.MemberSweep()

        if resultflag:
             await self.SendResult()

    def IsAutoExecutive(self):
        if self.channel is None: return False
        if self.active: return False
        if 0 < self.remainhp: return False
        return True

    @staticmethod
    def OverTime(remainhp : int, damage : int, overkill : bool):
        if overkill: return 0

        max = 90
        bonus = 20

        if damage <= 0: return 0

        d = max + 1 - (max * remainhp // damage) + bonus
        if max < d: return max
        return d

    def DefeatInfomation(self, slist : List[DamageControlMember], dcm : DamageControlMember, limit = 3):
        result = []
        thp = self.remainhp - dcm.damage

        i = 0

        found = False
        moverkill = dcm.member.IsOverkill()
        for s in slist:
            if dcm == s:
                found = True
                continue
                
            if thp <= s.damage:
                if s.member.IsOverkill() and (not found or not moverkill) : continue

                result.append( (s.member.name, self.OverTime(thp, s.damage, s.member.IsOverkill() )) )
                i += 1
                if limit <= i: break

        return result

    def DefeatCount(self, damagelist : List[DamageControlMember]):
        defeatcount = 1
        dsum = 0
        for n in damagelist:
            dsum += n.damage
            if self.remainhp <= dsum:
                break
            if 0 < n.damage and n.status == 0:
                defeatcount += 1
        
        return defeatcount

    def Status(self):
        mes = ''

        def Compare(a : DamageControlMember, b : DamageControlMember):
            ao = a.member.IsOverkill()
            bo = b.member.IsOverkill()

            if ao == bo: return sign(b.damage - a.damage)
            return sign(bo - ao)

        damagelist = sorted([value for value in self.members.values()], key=cmp_to_key(Compare)) 
        totaldamage = sum([n.damage for n in damagelist])

        attackmember = set([m for m in self.clanmembers.values() if m.attack])

        mes += '%s HP %d' % (BossName[self.bossindex] , self.remainhp)
        if 0 < totaldamage and totaldamage < self.remainhp:
            mes += '  不足分 %d' % (self.remainhp - totaldamage)
        else:
            defeatcount = self.DefeatCount(damagelist)
            if 3 <= defeatcount:
                last = damagelist[defeatcount - 1]
                namelist = []

                remainhp = self.remainhp
                for m in damagelist:
                    remainhp -= m.damage
                    if 0 < remainhp:
                        namelist.append(m.member.name + '[%d]' % remainhp)
                
                namelist.append(last.member.name)

                mes += '\n' + '→'.join(namelist)
                prevdamage = sum([damagelist[i].damage for i in range(defeatcount - 1) ])
                mes += ' %d秒' % self.OverTime(self.remainhp - prevdamage, last.damage, last.member.IsOverkill() )

        for m in damagelist:
            if m.status == 0:
                attackmember.discard(m.member)

                mes += '\n%s %d' % (m.member.DecoName('n[so]'), m.damage)
                if self.remainhp <= m.damage:
                    mes += ' %d秒' % (self.OverTime(self.remainhp, m.damage, m.member.IsOverkill()))
                else :
                    dinfo = self.DefeatInfomation(damagelist, m)
                    if 0 < len(dinfo):
                        mes += ''. join(['  →%s %d秒' % (d[0], d[1]) for d in dinfo])
                    else:
                        mes += '  残り %d' % (self.remainhp - m.damage)
        
        finishmember = [m.member.DecoName('n[so]') for m in damagelist if m.status != 0]

        if 0 < len(finishmember):
            mes += '\n通過済み %s' % (' '.join(finishmember))

        if 0 < len(attackmember):
            mes += '\n未報告 %s' % (' '.join([m.DecoName('n[so]') for m in attackmember]))
        return mes

    async def SendResult(self):
        if not self.active: return
        
        await self.SendMessage(self.Status())

    async def SendFinish(self, message):
        if not self.active: return

        if self.lastmessage is not None:
            await self.SendMessage(message)

        self.active = False
        self.lastmessage = None
        self.remainhp = 0
        self.members = {}

    async def SendMessage(self, mes):
        if self.outputlock == 1: return
        try:
            while self.outputlock != 0:
                await asyncio.sleep(1)

            if self.lastmessage is not None:
                self.outputlock = 1
                try:
                    await self.lastmessage.delete()
                except (discord.errors.NotFound, discord.errors.Forbidden):
                    pass
                self.lastmessage = None

            try:
                self.outputlock = 2
                self.lastmessage = await self.channel.send(mes)
            except discord.errors.Forbidden:
                self.channel = None
        finally:
            self.outputlock = 0
   
class Clan():
    numbermarks = [
        "\N{DIGIT ZERO}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT SIX}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT SEVEN}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT EIGHT}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT NINE}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
    ]

    emojis = [
        u"\u2705",
        "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT SIX}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT SEVEN}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT EIGHT}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        "\N{DIGIT NINE}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        u"\u274C",
    ]

    emojisoverkill = [
        u"\u2705",
        "\N{DIGIT ZERO}\N{COMBINING ENCLOSING KEYCAP}", # type: ignore
        u"\u274C",
    ]
    taskkillmark = u"\u2757"

    def __init__(self, channelid : int):
        self.members: Dict[int, ClanMember] = {}
        self.bosscount = 0
        self.channelid = channelid
        self.lastmessage : Optional[discord.Message] = None
        self.stampcheck :Dict[str, Any] = {}
        self.beforesortie = 0
        self.lap = {0 : 0.0}
        self.defeatlist = []
        self.attacklist = []
        self.namedelimiter = ''

        self.guild : discord.Guild = None
        self.inputchannel = None
        self.outputchannel = None

        self.damagecontrol = DamageControl(self.members)

        self.admin = False

        self.outputlock = 0

        self.commandlist = self.FuncMap()

    def FuncMap(self):
        return [
            (['a', '凸'], self.Attack),
            (['taskkill', 'タスキル'], self.TaskKill),
            (['memo', 'メモ'], self.Memo),
            (['prevboss'], self.PrevBoss),
            (['nextboss'], self.NextBoss),
            (['setboss'], self.SetBoss),
            (['notice', '通知'], self.Notice),
            (['reserve', '予約'], self.Reserve),
            (['refresh'], self.Refresh),
            (['memberlist'], self.MemberList),
            (['channellist'], self.ChannelList),
            (['namedelimiter'], self.NameDelimiter),
            (['memberinitialize'], self.MemberInitialize),
            (['setmemberrole'], self.SetMemberRole),
            (['role'], self.Role),
            (['reset'], self.MemberReset),
            (['history'], self.History),
            (['overtime', '持ち越し時間'], self.OverTime),
            (['gachaadd'], self.GachaAdd),
            (['gachadelete'], self.GachaDelete),
            (['gachalist'], self.GachaList),
            (['gacharate'], self.GachaRate),
            (['gacha10000'], self.Gacha10000),
            (['gacha', 'ガチャ'], self.Gacha),
            (['defeatlog'], self.DefeatLog),
            (['attacklog'], self.AttackLog),
            (['score'], self.Score),
            (['settingreload'], self.SettingReload),
            (['delete'], self.MemberDelete),
            (['dailyreset'], self.DailyReset),
            (['monthlyreset'], self.MonthlyReset),
            (['bossname'], self.BossName),
            (['term'], self.Term),
            (['remain','残り'], self.Remain),
            (['damage','ダメ','ダメージ'], self.Damage),
            (['pd'], self.PhantomDamage),
            (['dtest'], self.DamageTest),
            (['route', 'ルート'], self.Route),
            (['allroute', '全ルート'], self.AllRoute),
            (['clanattack'], self.AllClanAttack),
            (['clanreport'], self.AllClanReport),
            (['active', 'アクティブ'], self.ActiveMember),
            (['servermessage'], self.ServerMessage),
            (['serverleave'], self.ServerLeave),
            (['zeroserverleave'], self.ZeroServerLeave),
            (['inputerror'], self.InputError),
            (['gcmd'], self.GuildCommand),
        ]

    def GetMember(self, author) -> ClanMember:
        member = self.members.get(author.id)
        if (member is None):
            member = ClanMember()
            self.members[author.id] = member
        member.name = self.DelimiterErase(author.display_name)
        member.mention = author.mention
        return member

    def IsInput(self, channel_id):
        if self.inputchannel is None: return False
        return self.inputchannel.id == channel_id

    def FindMember(self, name) -> Optional[ClanMember]:
        for member in self.members.values():
            if (member.name == name):
                return member
        return None

    def DeleteMember(self, name) -> Optional[ClanMember]:
        for id, member in self.members.items():
            if (member.name == name):
                del self.members[id]
                return member
        return None

    def FullReset(self):
        self.Reset()
        self.bosscount = 0
        self.beforesortie = 0
        self.lap = {0 : 0.0}
        self.defeatlist.clear()
        self.attacklist.clear()
        self.RouteReset()

    def Reset(self):
        self.beforesortie = self.TotalSortie()
        self.lastmessage = None
        self.stampcheck = {}
        for member in self.members.values():
            member.Reset()

    def RouteReset(self):
        for member in self.members.values():
            member.route.clear()

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

    async def RemoveReaction(self, message, overkill : bool, me):
        reactemojis = self.emojis if not overkill else self.emojisoverkill

        for emoji in reactemojis:
            try:
                await message.remove_reaction(emoji, me)
            except (discord.errors.NotFound, discord.errors.Forbidden):
                break

    async def RemoveReactionNotCancel(self, message, overkill : bool, me):
        reactemojis = self.emojis if not overkill else self.emojisoverkill

        for emoji in reactemojis:
            if emoji != u"\u274C":
                try:
                    await message.remove_reaction(emoji, me)
                except (discord.errors.NotFound, discord.errors.Forbidden):
                    break

    async def SetNotice(self, member : ClanMember, message : discord.Message, bossstr : str):
        member.SetNotice(bossstr)

        if (member.notice is None):
            mark = self.numbermarks[0]
        else:
            mark = self.numbermarks[member.notice]

        await message.add_reaction(mark)

    async def Reserve(self, member : ClanMember, message : discord.Message, bossstr : str):
        pass

    async def MemberRefresh(self):
        if self.guild is None: return

        mes = ''
        mlist = []
        deletemember = []

        if len([m for m in self.guild.members if not m.bot]) < 40:
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
        else :
            mes += '人数が多すぎるので、自動調整は行なえません'

        for id in deletemember:
            del self.members[id]

        self.SetInputChannel()
        if self.inputchannel is not None:
            await self.inputchannel.send(mes)
    
    def CheckOptionNone(self, opt):
        if 0 < len(opt): 
            raise ValueError
        return True

    def CheckInputChannel(self, message):
        if self.inputchannel is None or message.channel.name != inputchannel:
            return True
            
        return False

    def CheckNotAdministrator(self, message):
        if message.author.guild_permissions.administrator:
            return False
        return True

    def CheckNotMasterAdministrator(self, clan, message):
        if clan.Admin:
            return False
        if message.author.guild_permissions.administrator:
            return False
        return True

    def AttackNum(self):
        return len([m for m in self.members.values() if m.attack])

    async def Attack(self, message, member : ClanMember, opt):
        self.CheckOptionNone(opt)

        if self.CheckInputChannel(message):
            await message.channel.send('%s のチャンネルで発言してください' % inputchannel)
            return False

        tmpattack = member.attackmessage if member.attack else None

        member.Attack(self)

        if 2 <= self.AttackNum():
            if  self.damagecontrol.IsAutoExecutive():
                try:
                    enemyhp = BossHpData[self.BossLevel() - 1][self.BossIndex()][0]
                    self.damagecontrol.RemainHp(self.BossIndex(), enemyhp)
                    await self.damagecontrol.TryDisplay()
                except IndexError:
                    pass


        if (member.taskkill != 0):
            await message.add_reaction(self.taskkillmark)

        member.attackmessage = message
        await self.AddReaction(message, member.IsOverkill())

        if tmpattack is not None:
            await self.RemoveReactionNotCancel(tmpattack, member.IsOverkill(), message.guild.me)

        return True

    async def TaskKill(self, message, member : ClanMember, opt):
        member.taskkill = message.id
        await message.add_reaction(self.taskkillmark)
        return True

    async def PrevBoss(self, message, member : ClanMember, opt):
        await self.ChangeBoss(message.channel, -1)
        return True

    async def NextBoss(self, message, member : ClanMember, opt):
        await self.ChangeBoss(message.channel, 1)
        return True

    async def SetBoss(self, message, member : ClanMember, opt):
        try:
            sp = opt.split(' ')
            if 2 <= len(sp):
                lap = int(sp[0])
                boss = int(sp[1])

                if 1 <= lap and 1 <= boss and boss <= BOSSNUMBER:
                    self.bosscount = (lap - 1) * BOSSNUMBER + boss - 1
                    await self.ChangeBoss(message.channel, 0)
                else:
                    raise ValueError

        except ValueError:
            await message.channel.send('数値エラー')

        return True

    async def Memo(self, message, member : ClanMember, opt):
        member.SetMemo(opt)
        return True

    async def Notice(self, message, member : ClanMember, opt):
        await self.SetNotice(member, message, opt)
        return False

    async def Refresh(self, message, member : ClanMember, opt):
        await self.MemberRefresh()
        return True

    async def MemberList(self, message, member : ClanMember, opt):

        if 0 < len(message.guild.members):
            await message.channel.send('\n'.join([m.name for m in message.guild.members]))
        else:
            await message.channel.send('len(message.guild.members):%d' % len(message.guild.members))

        return False

    async def ChannelList(self, message, member : ClanMember, opt):
        mes = ''
        mes += 'len %d\n' % (len(message.guild.channels))

        for m in message.guild.channels:
            mes += '%s/%s\n' % (m.name, m.name == inputchannel)

        await message.channel.send(mes)

        return False

    def DelimiterErase(self, name : str):
        if self.namedelimiter is None or self.namedelimiter == "":
            return name

        npos = name.find(self.namedelimiter)
        if npos < 0:
            return name
        return name[0:npos]

    async def NameDelimiter(self, message, member : ClanMember, opt):
        self.namedelimiter = None  if opt == '' else opt

        for m in self.guild.members:
            if m.id in self.members:
                self.members[m.id].name = self.DelimiterErase(m.display_name)

        if self.namedelimiter is None:
            mes = 'デリミタをデフォルトに戻しました'
        else:
            mes = 'デリミタを%sに設定しました' % self.namedelimiter

        await message.channel.send(mes)

        return True

    async def MemberInitialize(self, message, member : ClanMember, opt):
        if not message.author.guild_permissions.administrator: return False

        self.members.clear()
        await message.channel.send('メンバーを全て削除しました')

        return True

    async def SetMemberRole(self, message, member : ClanMember, opt):
        rolelist = [role for role in self.guild.roles if opt in role.name]

        if len(rolelist) == 0:
            await message.channel.send('Roleが見つかりません')
            return False
        elif 2 <= len(rolelist):
            await message.channel.send('Roleが複数あります %s' % (','.join([m.name for m in rolelist])) )
            return False

        role = rolelist[0]
        if len(role.members) == 0:
            await message.channel.send('Roleメンバーが0人です')
            return False

        self.members.clear()

        for m in role.members:
            if not m.bot:
                self.GetMember(m)

        await message.channel.send('%s のRoleのメンバーを登録しました' % role.name)

        return True

    async def Role(self, message, member : ClanMember, opt):
        rolelist = [('%s:%s' %(role.name, ','.join([m.name for m in role.members]))) for role in self.guild.roles]
        await message.channel.send('\n'.join(rolelist))

        return True

    async def CmdReset(self, message, member : ClanMember, opt):
        member.Reset()
        return True

    async def History(self, message, member : ClanMember, opt):
        if (opt == ''):
            await message.channel.send(member.History())
        else:
            fmember = self.FindMember(opt)
            if fmember is not None:
                await message.channel.send(fmember.History())
            else:
                await message.channel.send('メンバーがいません')
        return False

    async def OverTime(self, message, member : ClanMember, opt):
        try:
            time = int(opt)
            if time < 0 or 90 < time:
                raise ValueError
            errmes = member.ChangeOvertime(time)
            if errmes is not None:
                await message.channel.send(errmes)
                return False
            await message.channel.send('持ち越し時間を%d秒にしました' % time)
            return True
        except ValueError:
            await message.channel.send('時間が読み取れません')
            return False

        return True

    async def Gacha(self, message, member : ClanMember, opt):
        self.CheckOptionNone(opt)

        if (IsClanBattle()):
            return False
        else:
            await member.Gacha(message.channel)
            return False

    async def Gacha10000(self, message, member : ClanMember, opt):
        if (IsClanBattle()):
            return False
        else:
            await member.Gacha10000(message.channel)
            return False

    async def DefeatLog(self, message, member : ClanMember, opt):
        text = ''
        for n in self.defeatlist:
            text += n + '\n'

        with StringIO(text) as bs:
            await message.channel.send(file=discord.File(bs, 'defeatlog.txt'))
        return False

    async def AttackLog(self, message, member : ClanMember, opt):
        text = ''
        for n in self.attacklist:
            text += n + '\n'

        with StringIO(text) as bs:
            await message.channel.send(file=discord.File(bs, 'attacklog.txt'))
        return False

    async def GachaList(self, message, member : ClanMember, opt):
        await message.channel.send(Gacha.GachaScheduleData())
        return False

    async def GachaRate(self, message, member : ClanMember, opt):
        await message.channel.send(gacha.ToString())
        return False

    async def Score(self, message, member : ClanMember, opt):
        result = self.ScoreCalc(opt)
        if (result is not None):
            await message.channel.send('%d-%d %s (残りHP %s %%)' % 
            (result.lap, result.bossindex + 1, BossName[result.bossindex], result.hprate))
            return True
        else:
            await message.channel.send('計算できませんでした')
            return False
    
    async def Route(self, message, member : ClanMember, opt):
        channel = message.channel
        route = set()
        for n in opt:
            try:
                r = int(n)
                if 1 <= r and r <= 5:
                    route.add(r)
            except ValueError:
                pass

        member.route = list(route)               

        if 0 < len(member.route):
            await channel.send('凸ルート:' + ' '.join([BossName[i  - 1] for i in route]))
        else:
            await channel.send('凸ルートをリセットしました')

        return True

    async def AllRoute(self, message, member : ClanMember, opt):
        channel = message.channel
        s = ''

        bossroute = [[], [], [], [], []]
        for m in self.members.values():
            for r in m.route:
                if 0 < r and r <= len(bossroute):
                    bossroute[r - 1].append(m.name)

        for i, names in enumerate(bossroute):
            if 0 < len(names):
                s += '%s %d人 ' % (BossName[i], len(names))
                s += ' '.join([name for name in names]) + '\n'

        await channel.send(s)
        return False

    async def SettingReload(self, message, member : ClanMember, opt):
        channel = message.channel

        GlobalStrage.Load()
        gacha.BoxReset()
        await channel.send('リロードしました')
        await channel.send('term %s-%s' % (BATTLESTART, BATTLEEND))

        return False

    async def MemberDelete(self, message, member : ClanMember, opt):
        if not message.author.guild_permissions.administrator:
            return False

        result = self.DeleteMember(opt)
        if (result is not None):
            await message.channel.send('%s を消しました' % result.name)
            return True
        else:
            await message.channel.send('メンバーがいません')
            return False

    async def MemberReset(self, message, member : ClanMember, opt):
        member.Reset()
        return True

    async def DailyReset(self, message, member : ClanMember, opt):
        if not message.author.guild_permissions.administrator:
            return False

        self.Reset()
        return True

    async def MonthlyReset(self, message, member : ClanMember, opt):
        if not message.author.guild_permissions.administrator:
            return False

        self.FullReset()
        return True

    async def BossName(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False
        channel = message.channel

        namearray = opt.split(',')

        if BOSSNUMBER != len(namearray):
            await channel.send('usage) bossname boss1,boss2,boss3,boss4,boss5')
            return
        
        global BossName
        BossName = namearray
        GlobalStrage.Save()

        await channel.send('ボスを更新しました'+','.join(BossName))
        return True

    async def Term(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False
        channel = message.channel

        team = opt.split(',')

        if len(team) != 2:
            await channel.send('usage) team 1/20,1/30')
            return

        global BATTLEPRESTART
        global BATTLESTART
        global BATTLEEND

        try:
            start = datetime.datetime.strptime(team[0], '%m/%d')
            end = datetime.datetime.strptime(team[1], '%m/%d')

            BATTLEPRESTART = (start + datetime.timedelta(days = -1)).strftime('%m/%d')
            BATTLESTART = start.strftime('%m/%d')
            BATTLEEND = end.strftime('%m/%d')

            GlobalStrage.Save()
            await channel.send('クラバト期間は%s-%sです' % (BATTLESTART, BATTLEEND))
        except ValueError:
            await channel.send('日付エラーです')
        return True

    async def GachaAdd(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        channel = message.channel

        gtype = opt[0]
        date = opt[1:20]
        name = opt[20:]
        mes = '%s [%s] [%s]' % (Gacha.GachaType(gtype), date, name)

        if gtype not in '123dlpf':
            await channel.send(mes + ' ガチャタイプが不正です')
            return

        if not re.match('[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]', date):
            await channel.send(mes + ' 日付が不正です')
            return

        namearray = name.split(',')
        if 2 <= len(namearray):
            name = namearray

        for nitem in namearray:
            p = gacha.FindPrincess(nitem)
            if gtype == '3' and p not in '0':
                mes += '\n警告：%s は新規ではありません' % nitem
            if gtype == 'f' and p not in 'f0':
                mes += '\n警告：%s はプリフェス以外で登録されています' % nitem
            if gtype == 'l' and p not in 'l0':
                mes += '\n警告：%s は限定以外で登録されています' % nitem
            if gtype == 'p' and p not in 'l321':
                mes += '\n警告：%s は未登録かフェス限定のキャラです' % nitem

        global GachaData
        GachaData.append(GachaSchedule(date, gtype, name))
        GlobalStrage.Save()

        await channel.send(mes)
        return False

    async def GachaDelete(self, message, member : ClanMember, opt):
        channel = message.channel

        global GachaData
        try:
            gindex = int(opt)
            if 0 < gindex and gindex <= len(GachaData):
                GachaData.pop(-gindex)
                GlobalStrage.Save()
                await channel.send(Gacha.GachaScheduleData())
                return
        except ValueError:
            pass
        await channel.send('数値変換に失敗しました')
        return False

    async def AllClanAttack(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        channel = message.channel

        mes = ''
        for guild in client.guilds:
            clan = clanhash.get(guild.id)
            if clan is not None:
                attackmembers = [m.name for m in clan.members.values() if m.attack]
                atn = len(attackmembers)
                if 0 < atn:
                    mes += '[%s] %d %s\n' % (guild.name, atn, ' '.join(attackmembers))

        await channel.send(mes)

        return False

    async def AllClanReport(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        channel = message.channel

        mes = ''
        for guild in client.guilds:
            mes += '[%d] %s\n' % (guild.id, guild.name)

            clan = clanhash.get(guild.id)
            if clan is not None:
                mes += clan.Status() + '\n'

        dt_now = datetime.datetime.now()
        filename = 'report_%s.txt' % dt_now.strftime("%Y%m%d_%H%M")  
        
        with StringIO(mes) as bs:
            await channel.send(file=discord.File(bs, filename))

        return False

    async def ActiveMember(self, message, member : ClanMember, opt):
        channel = message.channel

        mes = ''

        ttime = datetime.datetime.now() + datetime.timedelta(hours = -1)
        active = [m for m in self.members.values() if ttime < m.lastactive and m.SortieCount() < MAX_SORITE]

        def Compare(a : ClanMember, b : ClanMember):
            return sign(a.SortieCount() - b.SortieCount())

        active = sorted(active, key=cmp_to_key(Compare))

        for m in active:
            mes += '%s: %d凸' % (m.name, m.SortieCount())
            if m.IsOverkill():
                mes += '[%s:%d秒]' % (BossName[m.Overboss() % BOSSNUMBER], m.Overtime())
            mes += '\n'

        await channel.send(mes)
        return False

    async def InputError(self, message, member : ClanMember, opt):
        for clan in clanhash.values():
            clan.SetInputChannel()
            if clan.inputchannel is None:
                await message.channel.send('%s[%d]' % (clan.guild.name, clan.guild.id))

        return False

    async def ServerMessage(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        s = opt.split(' ')

        if len(s) < 2:
            await message.channel.send('オプションがありません')
            return False

        try:
            gindex = int(s[0])
        except ValueError:
            await message.channel.send('guildidが違います')
            return False

        if gindex in clanhash:
            clan = clanhash[gindex]

            clan.SetInputChannel()
            if clan.inputchannel is None:
                await message.channel.send('inputchannel が設定されていません')
                return False
            
            await clan.inputchannel.send(s[1])
        else:
            await message.channel.send('guildがありません')
        
        return False

    async def ServerLeave(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        try:
            gindex = int(opt)
        except ValueError:
            await message.channel.send('guildidが違います')
            return False

        if gindex in clanhash:
            clan = clanhash[gindex]

            await clan.guild.leave()
            return False

        guildlist = [g for g in client.guilds if g.id == gindex]
        if 1 <= len(guildlist):
            await guildlist[0].leave()
            return False

        await message.channel.send('guildがありません')
        return False

    async def ZeroServerLeave(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        server = []

        for clan in clanhash.values():
            if clan.bosscount == 0:
                server.append(clan.guild)

        for clan in server:
            await clan.leave()

        return False

    async def GuildList(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        guildname = opt

        global client

        if guildname == '':
            guildlist = [(idx, guild) for idx, guild in enumerate(client.guilds) if idx < 10]
        else:
            guildlist = [(idx, guild) for idx, guild in enumerate(client.guilds) if guildname in guild.name]

        await message.channel.send('\n'.join(['%d:%s' % (m[0], m[1].name) for m in guildlist]))

        return False

    async def GuildCommand(self, message, member : ClanMember, opt):
        if not self.admin: return False
        if not message.author.guild_permissions.administrator: return False

        return False

    async def Remain(self, message, member : ClanMember, opt):
        if message.channel.type == discord.ChannelType.private:
            await message.channel.send('このチャンネルでは使えません')
            return

        try:
            remainhp = int(opt)
        except ValueError:
            await message.channel.send('数字が読み取れません')
            return False

        if 0 < remainhp:
            self.damagecontrol.SetChannel(message.channel)
            self.damagecontrol.RemainHp(self.BossIndex(), remainhp)
            await self.damagecontrol.SendResult()
        else:
            await self.damagecontrol.SendFinish('キャンセルしました')

        return False

    async def Damage(self, message, member : ClanMember, opt):
        if message.channel.type == discord.ChannelType.private:
            await message.channel.send('このチャンネルでは使えません')
            return
        
        try:
            damage = int(opt)
        except ValueError:
            damage = 0

        if not self.damagecontrol.active:
            await message.channel.send('ダメコンを行っていません')
            return 
        self.damagecontrol.Damage(member, damage)
        await self.damagecontrol.SendResult()
        return False

    @staticmethod
    def GetIndexValue(d : Dict, idx : int):
        i = 0
        for value in d.values():
            if i == idx:
                return value
            i += 1
        return None

    async def PhantomDamage(self, message, member : ClanMember, opt):
        if message.channel.type == discord.ChannelType.private:
            await message.channel.send('このチャンネルでは使えません')
            return
        
        try:
            sp = opt.split(' ')
            damage = int(sp[0])
            m = int(sp[1])
        except ValueError:
            damage = 0
            m = 0

        if not self.damagecontrol.active:
            await message.channel.send('ダメコンを行っていません')
            return 
        
        mem = self.GetIndexValue(self.members, m)
        if mem is None: mem = member

        self.damagecontrol.Damage(mem, damage)
        await self.damagecontrol.SendResult()

    async def DamageTest(self, message, member : ClanMember, opt):
        
        mem = self.GetIndexValue(self.members, 1)
        if mem is None: mem = member
        mem.name = 'ダイチ'
        self.damagecontrol.Damage(mem, 600)

        mem = self.GetIndexValue(self.members, 2)
        if mem is None: mem = member
        mem.name = 'アサヒ'
        self.damagecontrol.Damage(mem, 800)

        mem = self.GetIndexValue(self.members, 3)
        if mem is None: mem = member
        mem.name = 'ミタカ'
        self.damagecontrol.Damage(mem, 740)

        await self.damagecontrol.SendResult()


    def ScoreCalc(self, opt):
        try:
            score = int(opt)
            return ClanScore.Calc(score)

        except ValueError:
            return None
    
    def FindChannel(self, guild : discord.Guild, name : str) -> Optional[discord.TextChannel]:
        if guild is None or guild.channels is None:
            return None
        for channel in guild.channels:
            if channel.name == name:
                return client.get_channel(channel.id)
        return None

    def AllowMessage(self, message):
        if message.channel.name == inputchannel: return True
        if message.guild.me in message.mentions: return True

        return False

    def SetOutputChannel(self):
        if self.outputchannel is None:
            self.outputchannel = self.FindChannel(self.guild, outputchannel)

    def SetInputChannel(self):
        if self.inputchannel is None:
            self.inputchannel = self.FindChannel(self.guild, inputchannel)

    async def on_message(self, message):
        if self.AllowMessage(message):
            member = self.GetMember(message.author)
            member.UpdateActive()

            content = re.sub('<[^>]*>', '', message.content).strip()

            if message.channel.name == inputchannel:
                self.inputchannel = message.channel

            self.SetOutputChannel()
            if self.outputchannel is None:
                await message.channel.send('%s というテキストチャンネルを作成してください' % (outputchannel))
                return False

            for cmdtuple in self.commandlist:
                for cmd in cmdtuple[0]:
                    opt = Command(content, cmd)
                    if opt is not None:
                        try:
                            return await cmdtuple[1](message, member, opt)
                        except ValueError:
                            pass
        
        if self.damagecontrol.active and self.damagecontrol.channel == message.channel:
            member = self.GetMember(message.author)
            if member.attack:
                try:

                    dmg = int(message.content)
                    if 0 <= dmg:
                        await self.Damage(message, member, message.content)
                except ValueError:
                    pass
            return False

        member = self.members.get(message.author.id)
        if member is not None:
            member.UpdateActive()

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

        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        if l < count:
            for _i in range(count - l):
                self.defeatlist.append(now)
        
        self.defeatlist[count - 1] = now

    def AddAttackTime(self, count):
        icount = int(count)
        l = len(self.attacklist)

        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        if l <= icount:
            for _i in range(icount + 1 - l):
                self.attacklist.append(now)
        
        self.attacklist[icount] = now

    async def ChangeBoss(self, channel, count):
        await self.damagecontrol.SendFinish('%s の討伐お疲れさまです' % (BossName[self.BossIndex()]))

        self.bosscount += count
        if (self.bosscount < 0):
            self.bosscount = 0
        await channel.send('次のボスは %s です' % (BossName[self.BossIndex()]) )

        if (0 <= count):
            self.AddDefeatTime(self.bosscount)

            if (self.BossIndex() == 0):
                self.lap[self.BossLap() - 1] = self.TotalSortie()

            notice = self.CreateNotice(self.BossIndex())
            if (notice is not None):
               await channel.send('%s %s がやってきました' % (notice, BossName[self.BossIndex()]))

            if self.BossIndex() == 0 and self.BossLap() in LevelUpLap:
                self.RouteReset()

    async def on_raw_reaction_add(self, payload):
        member = self.members.get(payload.user_id)
        if member is None:
            return False

        if self.inputchannel is None or self.inputchannel.id != payload.channel_id:
            return False

        if member.attackmessage is None or member.attackmessage.id != payload.message_id:
            return False

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
            self.AddAttackTime(self.TotalSortie())

            member.Finish(self, payload.message_id)
            member.notice = None
            await self.damagecontrol.Injure(member)
        
        if (1 <= idx and idx <= 8):
            self.AddAttackTime(self.TotalSortie())

            boss = member.boss
            if (overkill):
                member.Finish(self, payload.message_id, True)
            else:
                member.Overkill(self, (idx + 1) * 10, payload.message_id)

            member.notice = None

            if (self.bosscount == boss):
                if self.inputchannel is not None:
                    await self.ChangeBoss(self.inputchannel, 1)

            for m in self.members.values():
                if m.attack and m.boss == boss:
                    m.reportlimit = datetime.datetime.now() + datetime.timedelta(minutes = 5)
        
        if (idx == 9):
            member.Cancel(self)
            await self.damagecontrol.Remove(member)

        message = member.attackmessage
        await self.RemoveReaction(message, overkill, message.guild.me)
        return True

    async def on_raw_reaction_remove(self, payload):
        member = self.members.get(payload.user_id)
        if member is None:
            return False

        if self.inputchannel is None or self.inputchannel.id != payload.channel_id:
            return False

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

    def BossAverage(self, bossindex):
        nowlap = self.bosscount // BOSSNUMBER
        if nowlap == 0 or nowlap not in self.lap:
            return 0

        lvup = self.GetLevelUpLap(nowlap)

        defeatlist = [(self.lap[l - 2] - self.lap[l - 1])
            for l in range(lvup * BOSSNUMBER + bossindex - 1, self.bosscount, BOSSNUMBER)]

        if len(defeatlist) == 0:
            return 0

        return sum(defeatlist) / len(defeatlist)

    def BossIndex(self):
        return self.bosscount % BOSSNUMBER
    
    def BossLap(self):
        return self.bosscount // BOSSNUMBER + 1

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
        return (LevelUpLap[levelindex] - self.bosscount / BOSSNUMBER - 1)

    def Status(self):
        s = ''
        hpinfo = ''
        if self.damagecontrol.active:
            enemyhp = BossHpData[self.BossLevel() - 1][self.BossIndex()][0]
            if self.damagecontrol.remainhp < enemyhp:
                hpinfo = '[%d/%d]' % (self.damagecontrol.remainhp, enemyhp)

        s += '現在 %d-%d %s%s\n' % (self.BossLap(), self.BossIndex() + 1, BossName[self.BossIndex()], hpinfo)

        attackcount = 0
        count : List[List[ClanMember]] = [[], [], [], []]

        for member in self.members.values():
            count[member.SortieCount()].append(member)
            attackcount += member.SortieCount()

        attacklist = [m.DecoName('n[so]') for m in self.members.values() if m.attack]
        if 0 < len(attacklist):
            s += '攻撃中 %d人\n' % (len(attacklist)) + ' '.join(attacklist) + '\n'

        oklist = [m for m in self.members.values() if m.IsOverkill()]

        def Compare(a : ClanMember, b : ClanMember):
            an = a.Overboss()
            bn = b.Overboss()
            if (an - bn) % BOSSNUMBER == 0: 
                return sign(an - bn)
            return sign(an % BOSSNUMBER) - (bn % BOSSNUMBER)

        overkilllist = sorted(oklist, key=cmp_to_key(Compare))
        oknum = len(overkilllist)

        if 0 < oknum:
            s += '持ち越し %d人\n' % (oknum)
            s += ''.join(['%s\n' % m.OverKillMessage() for m in overkilllist])

        attackcount += oknum * 0.5
        restattack = len(self.members) * MAX_SORITE - attackcount
        lap = self.LapAverage()
        restlap = (restattack / lap) if 0 < lap else 0 

        nextlap = self.NextLvUpLap()
        nextstr = ''
        if 0 < nextlap and 0 < lap:
            nextstr = ' / %d段階目まで%.1f凸' % (self.BossLevel() + 1, nextlap * lap)

        def fout(n :float):
            if n % 1 == 0: return '%d' % n
            else: return '%0.1f' % n

        s += '\n'

        s += '総攻撃数 %s回 (残り %s回 約%.1f周%s)\n' % (fout(attackcount), fout(restattack), restlap, nextstr)

        for i, c in enumerate(count):
            if 0 < len(c):
                slist = sorted(c, key=lambda member : member.lastactive, reverse=True)
                s += '%d回目 %d人\n' % (i, len(c))
                s += '  '.join([m.DecoName('nOT') for m in slist]) + '\n'
        
        routedisplay = False
        bossroute = [[], [], [], [], []]
        for m in self.members.values():
            route = m.GetUnfinishRoute()

            for r in route:
                bossroute[r - 1].append(m.name)
                routedisplay = True

        if routedisplay:
            s += '\nルート宣言\n'
            for i, names in enumerate(bossroute):
                if 0 < len(names):
                    s += '%s %d人 ' % (BossName[i], len(names))
                    s += ' '.join([name for name in names]) + '\n'

        return s

    @staticmethod
    def Save(clan, clanid):
        dic = {
            'members': {},
            'bosscount' : clan.bosscount,
            'channelid' : clan.channelid,
            'beforesortie' : clan.beforesortie,
            'lap' : clan.lap,
            'defeatlist' : clan.defeatlist,
            'attacklist' : clan.attacklist,
            'namedelimiter' : clan.namedelimiter,
            'admin' : clan.admin,
        }

        for mid, member in clan.members.items():
            dic['members'][mid] = member.Serialize()

        with open('clandata/%d.json' % (clanid) , 'w') as a:
            json.dump(dic, a , indent=4)

    @staticmethod
    def Load(clanid):
        with open('clandata/%d.json' % (clanid)) as a:
            mdic =  json.load(a)

            clan = Clan(mdic['channelid'])
            clan.bosscount = mdic['bosscount']
            clan.namedelimiter = mdic['namedelimiter'] if 'namedelimiter' in mdic else None

            if 'beforesortie' in mdic:
                clan.beforesortie = mdic['beforesortie']
            
            if 'defeatlist' in mdic:
                clan.defeatlist = mdic['defeatlist']

            if 'attacklist' in mdic:
                clan.attacklist = mdic['attacklist']

            if 'lap' in mdic:
                for key, value  in mdic['lap'].items():
                    clan.lap[int(float(key))] = value

            if 'admin' in mdic:
                clan.admin = mdic['admin']

            for mid, dicmember in mdic['members'].items():
                member = ClanMember()
                member.Deserialize(dicmember)
                clan.members[int(mid)] = member

            return clan


    

class PrivateUser:
    DefalutHave = set()

    def __init__(self, channel, author):
        self.id = author.id if author is not None else 0
        self.channel = channel
        self.author = author
        self.guildid = 0
        self.clan : Optional[Clan] = None
        self.have = set()
        self.unhave = set()

        self.used = set()
        self.cachehavelist  = set()
        self.cacheunusedlist = set()
        
    def IsHave(self, princessid):
        if princessid in self.cachehavelist:
            return True
        else :
            return False

    def RegiseterPrincess(self, pindex: int, haveflag: bool):
        if haveflag:
            if pindex not in self.DefalutHave:
                self.have.add(pindex)
            self.unhave.discard(pindex)
        else:
            self.have.discard(pindex)
            self.unhave.add(pindex)

        self.UpdateHaveList()

    def RegisterList(self, havelist : List[int], unhavelist: List[int]):
        for pindex in havelist:
            if pindex not in self.DefalutHave:
                self.have.add(pindex)
            self.unhave.discard(pindex)
        
        for pindex in unhavelist:
            self.have.discard(pindex)
            self.unhave.add(pindex)

        self.UpdateHaveList()

    def Used(self, usedlist : List[int], unusedlist : Optional[List[int]] = None):
        for n in usedlist:
            self.used.add(n)
        if unusedlist is not None:
            for n in unusedlist:
                self.used.discard(n)
        self.UpdateUnusedList()

    def UsedClear(self):
        self.used.clear()
        self.UpdateUnusedList()

    def UpdateHaveList(self):
        self.cachehavelist = (self.DefalutHave | self.have) - self.unhave
        self.UpdateUnusedList()

    def UpdateUnusedList(self):
        self.cacheunusedlist = self.cachehavelist - self.used

    async def ClanCheck(self, channel : discord.channel):
        if self.clan is None:
            clanlist = PrivateMessage.GetClanList(self.id)
            if len(clanlist) == 1:
                await channel.send('%s のクランを参照します')
                self.clan = clanlist[0]
                self.guildid = self.clan.guild.id
                return True
            else:
                mes = ''
                mes += 'clan [クラン名] でクランを設定してください\n'
                cnamelist = [clan.guild.name for clan in clanlist if clan.guild is not None]
                mes += ','.join(cnamelist)
                await channel.send(mes)
                return False
        return True


    def Serialize(self):
        dic = {
            'id' : self.id,
            'guildid': self.guildid,
            'have' : list(self.have),
            'unhave' : list(self.unhave),
            'used' : list(self.used)
        }

        return dic

    @staticmethod
    def Deserialize(data):
        ret = PrivateUser(None, None)

        for key in ['id', 'guildid']:
            if key in data:
                ret.__dict__[key] = data[key]

        for key in ['have', 'unhave', 'used']:
            if key in data:
                ret.__dict__[key] = set(data[key])

        ret.UpdateHaveList()
        ret.UpdateUnusedList()

        return ret

    @staticmethod
    def DefalutHaveLoad():
        with open('defaulthave.txt') as f:
            for s_line in f:
                n = princessIndex.GetIndex(s_line.strip())
                if 0 < n:
                    PrivateUser.DefalutHave.add(n)
                else:
                    print('Unknown name %s' % s_line)

    @staticmethod
    def SaveList(userdic):
        deserializedlist = {}
        for key,value in userdic.items():
            deserializedlist[key] = value.Serialize()

        with open('user.json', 'w') as a:
            json.dump(deserializedlist, a , indent=4)


    @staticmethod
    def LoadList(userdic):
        try:
            with open('user.json') as a:
                mdic =  json.load(a)
                for key,value in mdic.items():
                    userdic[int(key)] = PrivateUser.Deserialize(value)
        except FileNotFoundError:
            pass

PrivateUser.DefalutHaveLoad()

userhash: Dict[int, PrivateUser] = {}

PrivateUser.LoadList(userhash)

class PartyInfoList:
    def __init__(self):
        self.plist :List[PartyInfomation] = []

    def Append(self, pinfo : PartyInfomation):
        index = len(self.plist)
        pinfo.index = index
        self.plist.append(pinfo)
        return index

    def Delete(self, userid, index):
        if 0 <= index and index < len(self.plist):
            if self.plist[index].userid== userid:
                self.plist[index].share = -1
    
    def Serialize(self):
        serial = {
            'plist' : [m.Serialize() for m in self.plist]
        }

        return serial

    @staticmethod
    def Deserialize(list):
        des = PartyInfoList()
        if 'plist' in list:
            des.plist = [PartyInfomation.Deserialize(m) for m in list['plist']]
        
        return des

class PartyInfoNotepad:
    def __init__(self):
        self.notepad : Dict[int, PartyInfoList] = {}
   
    def Register(self, party : PartyInfomation):
        partylist = self.notepad.get(party.boss)
        if partylist is None:
            partylist = PartyInfoList()
            self.notepad[party.boss] = partylist
        
        partylist.Append(party)

    @staticmethod
    def SameExist(partylist, party : set) -> bool:
        for p in partylist:
            if 5 <= p.PartyMatch(party):
                return True
        
        return False

    def List(self, boss, party: Optional[set], userid) -> List[PartyInfomation]:
        partylist = self.notepad.get(boss)
        if partylist is None:
            return []
        
        result : List[PartyInfomation] = []
        for p in partylist.plist:
            if not p.Viewable(userid): continue
            if party is not None and p.PartyMatch(party) < len(party): continue
#            if self.SameExist(result, p.party): continue

            result.append(p)
            if  9 <= len(result): break

        return result

    def Infomation(self, index, userid) -> Optional[PartyInfomation]:
        devide = 1000

        partylist = self.notepad.get(index // devide)

        if partylist is None:
            return None
        
        n = index % devide
        if n < 0 or len(partylist.plist) <= n: return None
        info = partylist.plist[n]
        if info.Viewable(userid):
            return info
        return None

    def Modify(self, index, userid, memo)-> Optional[PartyInfomation]:
        infomation = self.Infomation(index, userid)
        if infomation is None: return None
        if infomation.userid != userid: return None

        infomation.memo = memo
        return infomation

    def Delete(self, index, userid):
        infomation = self.Infomation(index, userid)
        if infomation is None: return None
        if infomation.userid != userid: return None

        infomation.share = -1
        return infomation

    def Serialize(self):
        serial = {}

        for key, value in self.notepad.items():
            serial[key] = value.Serialize()

        return {
            'PartyInfoNotepad': serial
        }

    @staticmethod
    def Deserialize(list):
        des = PartyInfoNotepad()
        if 'PartyInfoNotepad' in list:
            for key, value in list['PartyInfoNotepad'].items():
                des.notepad[int(key)] = PartyInfoList.Deserialize(value)
        
        return des

    def Save(self):
        PartyInfoNotepadSerialize = self.Serialize()

        with open(PARTYFILE, 'w') as a:
            json.dump(PartyInfoNotepadSerialize, a , indent=4)

    @staticmethod
    def Load():
        try:
            with open(PARTYFILE, 'r') as a:
                mdic =  json.load(a)
                return PartyInfoNotepad.Deserialize(mdic)
        except FileNotFoundError:
            return PartyInfoNotepad()

partyInfoNotepad = PartyInfoNotepad.Load()

class PrivateMessage:

    @staticmethod
    def RecomendDisplay(user :PrivateUser, boss: int, listnum : int):
        bosslevel = boss // 10
        bossindex = boss % 10 - 1
        mes = ''
        result = partyInfoNotepad.List(boss, None, user.author.id)
        displist = [n for n in result if len(n.party) - 1 <= n.PartyMatch(user.cacheunusedlist)]
        mes += '%d-%d:%s %d\n' % (bosslevel, bossindex + 1, BossName[bossindex], len(displist))
        for n, disp in enumerate(displist):
            if listnum <= n: break
            mes += disp.InfoOneLineRecomend(user.cacheunusedlist) + '\n'
        
        return mes

    @staticmethod
    async def Recomend(user: PrivateUser, channel : discord.channel, message : str):
        await user.ClanCheck(channel)
        if user.clan is None: return

        try:
            bosslevel = int(message)
        except ValueError: 
            bosslevel = user.clan.BossLevel()

        mes = ''
        if bosslevel <= 4:
            for i in range(BOSSNUMBER):
                boss = bosslevel * 10 + i + 1
                mes += PrivateMessage.RecomendDisplay(user, boss, 3)
        else:
            bn = bosslevel % 10 - 1
            if 0 <= bn and bn < BOSSNUMBER:
                mes += PrivateMessage.RecomendDisplay(user, bosslevel, 9)
            else:
                mes += 'ボス番号エラー'

        await channel.send(mes)

    @staticmethod
    def ListDisplay(user :PrivateUser, boss: int, listnum : int, party: Optional[set]):
        bosslevel = boss // 10
        bossindex = boss % 10 - 1
        mes = ''
        displist = partyInfoNotepad.List(boss, party, user.author.id)
        mes += '%d-%d:%s %d\n' % (bosslevel, bossindex + 1, BossName[bossindex], len(displist))
        for n, disp in enumerate(displist):
            if listnum <= n: break
            mes += disp.InfoOneLine() + '\n'
        
        return mes

    @staticmethod
    async def List(user: PrivateUser, channel : discord.channel, message: str):
        await user.ClanCheck(channel)
        if user.clan is None: return

        meslist = message.split()
        try:
            bosslevel = int(meslist[0])
        except (ValueError, IndexError):
            bosslevel = user.clan.BossLevel()

        if 100 <= bosslevel:
            await PrivateMessage.Info(user, channel, message)
            return

        party = None
        if 1 < len(meslist):
            partylist = princessIndex.Chopper(' '.join(meslist[1:]))
            if partylist is None:
                await channel.send('パーティの解析失敗')
                return
            party = set(partylist)


        mes = ''
        if bosslevel <= 4:
            for i in range(BOSSNUMBER):
                boss = bosslevel * 10 + i + 1
                mes += PrivateMessage.ListDisplay(user, boss, 3, party)
        else:
            bn = bosslevel % 10 - 1
            if 0 <= bn and bn < BOSSNUMBER:
                mes += PrivateMessage.ListDisplay(user, bosslevel, 9, party)
            else:
                mes += 'ボス番号エラー'

        await channel.send(mes)

    @staticmethod
    async def PartyRegister(user: PrivateUser, channel : discord.channel, message: str):
        await user.ClanCheck(channel)
        if user.clan is None: return

        cr = message.find('\n')
        firstline = message[0:cr]
        memo = "" if cr < 0 else message[cr:-1].strip()

        try:
            boss = int(firstline[0:2])
            if boss // 10 < 0 or 4 < boss // 10 or boss % 10 <= 0 or BOSSNUMBER < boss % 10:
                raise ValueError
        except ValueError:
            await channel.send('ボス番号不正')
            return

        partyset = princessIndex.Chopper(firstline[3:])

        if partyset is None:
            await channel.send('パーティメンバーの解析失敗')
            return
        
        if 1800 < len(memo.encode('utf-8')):
            await channel.send('メモ欄が長すぎます')
            return

        n = PartyInfomation(boss, partyset, memo, 0, user.author.id)
        partyInfoNotepad.Register(n)
        partyInfoNotepad.Save()

        await channel.send(n.InfoOneLine())

    @staticmethod
    async def Check(user: PrivateUser, channel : discord.channel, message: str):
        result = princessIndex.Chopper(message)

        if result is None:
            await channel.send('パーティの解析失敗')
        else:
            await channel.send('/'.join(princessIndex.Convert2Name(result)))

    @staticmethod
    async def Info(user: PrivateUser, channel : discord.channel, message: str):
        await user.ClanCheck(channel)
        if user.clan is None: return

        try:
            boss = int(message)
        except ValueError:
            await channel.send('数値エラー')
            return
 
        result = partyInfoNotepad.Infomation(boss, user.author.id)

        if result is not None:
            mes = result.BossInfo() + '\n' + result.Infomation()
        else:
            mes = '見つかりません'
        await channel.send(mes)

    @staticmethod
    async def Modify(user: PrivateUser, channel : discord.channel, message: str):
        await user.ClanCheck(channel)
        if user.clan is None: return

        cr = message.find('\n')
        firstline = message[0:cr]
        memo = "" if cr < 0 else message[cr:-1].strip()
        try:
            boss = int(firstline)
        except ValueError:
            await channel.send('数値エラー')
            return
 
        result = partyInfoNotepad.Modify(boss, user.author.id, memo)

        if result is not None:
            mes = '%d の編成のメモを変更しました' % boss
        else:
            mes = '編成が見つかりません'
        await channel.send(mes)

    @staticmethod
    async def Delete(user: PrivateUser, channel : discord.channel, message: str):
        await user.ClanCheck(channel)
        if user.clan is None: return

        try:
            boss = int(message)
        except ValueError:
            await channel.send('数値エラー')
            return
 
        result = partyInfoNotepad.Delete(boss, user.author.id)

        if result is not None:
            mes = '%d の編成を削除しました' % boss
        else:
            mes = '編成が見つかりません'
        await channel.send(mes)

    @staticmethod
    def GetClanList(userid : int):
        clanlist:List[Clan] = []

        for clan in clanhash.values():
            if userid in clan.members:
                clanlist.append(clan)
        return clanlist

    @staticmethod
    def UserSave():
        global userhash
        PrivateUser.SaveList(userhash)

    @staticmethod
    async def SetClan(user : PrivateUser, channel, opt : str):
        clanlist = PrivateMessage.GetClanList(user.id)
        matchclan = [c for c in clanlist if c.guild is not None and c.guild.name == opt]

        if len(matchclan) == 0:
            await channel.send('クランが見つかりません')
            return

        def match(id, l):
            for m in l:
                if m.id == id: return True
            return False

        joinclan = [c for c in matchclan if match(user.id, c.guild.members)]

        if len(joinclan) == 0:
            await channel.send('あなたが属しているクランが見つかりません')
            return

        user.clan = joinclan[0]
        if user.clan is not None:
            user.guildid = user.clan.guild.id

        await channel.send('%s にクランを設定しました' % (opt))
        PrivateMessage.UserSave()

    @staticmethod
    async def Have(user: PrivateUser, channel : discord.channel, message: str):
        meslist = message.split()
        havelist = []
        unhavelist = []

        global princessIndex

        if len(meslist) == 0:
            mes = ''
            if 0 < len(user.have):
                havename = princessIndex.Convert2Name(user.have)
                mes += '所持:%s\n' % ','.join(havename)

            if 0 < len(user.unhave):
                unhavename = princessIndex.Convert2Name(user.unhave)
                mes += '未所持:%s\n' % ','.join(unhavename)

            if 0 < len(mes):
                await channel.send(mes)
            else:
                await channel.send('所持登録されてません')
            return

        for m in meslist:
            if 0 < len(m) and m[0] == '-':
                result = princessIndex.Chopper(m[1:])
                if result is None:
                    await channel.send('%s で解析失敗' % m)
                    return
                unhavelist.extend(result)
            else:
                result = princessIndex.Chopper(m)
                if result is None:
                    await channel.send('%s で解析失敗' % m)
                    return 
                havelist.extend(result)

        user.RegisterList(havelist, unhavelist)
        PrivateMessage.UserSave()

        mes = ''
        if 0 < len(havelist):
            havename = princessIndex.Convert2Name(havelist)
            mes += '所持追加:%s\n' % ','.join(havename)
        
        if 0 < len(unhavelist):
            unhavename = princessIndex.Convert2Name(unhavelist)
            mes += '未所持追加:%s\n' % ','.join(unhavename)
        await channel.send(mes)

    @staticmethod
    async def Use(user: PrivateUser, channel : discord.channel, message: str):
        meslist = message.split()

        global princessIndex

        if len(meslist) == 0:
            mes = ''
            if 0 < len(user.used):
                usedname = princessIndex.Convert2Name(user.used)
                mes += '使用:%s\n' % ','.join(usedname)

            if 0 < len(mes):
                await channel.send(mes)
            else:
                await channel.send('使用済みキャラがいません')
            return
        
        if message == 'reset':
            await PrivateMessage.UseReset(user, channel, message)
            return 

        try:
            boss = int(meslist[0])
        except ValueError:
            boss = 0

        usedlist = []
        unusedlist = []
        if 0 < boss:
            partyinfo = partyInfoNotepad.Infomation(boss, user.author.id)
            if partyinfo is None:
                await channel.send('%d の編成が見つかりません' % boss)
                return
            
            party = partyinfo.party.copy()

            if 1 < len(meslist):
                result = princessIndex.Chopper(meslist[1])
                if result is None:
                    await channel.send('%s で解析失敗' % meslist[1])
                    return
                if 0 < len(result):
                    party.discard(result[0])
            
            usedlist.extend(list(party))

        else:
            for m in meslist:
                if 0 < len(m) and m[0] == '-':
                    result = princessIndex.Chopper(m[1:])
                    if result is None:
                        await channel.send('%s で解析失敗' % m)
                        return
                    unusedlist.extend(result)
                else:
                    result = princessIndex.Chopper(m)
                    if result is None:
                        await channel.send('%s で解析失敗' % m)
                        return 
                    usedlist.extend(result)

        user.Used(usedlist, unusedlist)
        PrivateMessage.UserSave()

        mes = ''
        if 0 < len(usedlist):
            usedname = princessIndex.Convert2Name(usedlist)
            mes += '使用済み:%s\n' % ','.join(usedname)
        
        if 0 < len(unusedlist):
            unusedname = princessIndex.Convert2Name(unusedlist)
            mes += '未使用:%s\n' % ','.join(unusedname)
        await channel.send(mes)

    @staticmethod
    async def UseReset(user: PrivateUser, channel : discord.channel, message: str):
        user.UsedClear()
        PrivateMessage.UserSave()
        mes = '使用済みキャラをリセットしました'
        await channel.send(mes)

    @staticmethod
    async def on_message(user: PrivateUser, channel : discord.channel, message: str):
        Outlog('private.log', '[%s]%s' % (user.author.name, message) )

        opt = Command(message, 'clan')
        if opt is not None:
            await PrivateMessage.SetClan(user, channel, opt)
            return True

        opt = Command(message, 'party')
        if opt is not None:
            await PrivateMessage.PartyRegister(user, channel, opt)
            return True

        opt = Command(message, ['おすすめ', 'reco'])
        if opt is not None:
            await PrivateMessage.Recomend(user, channel, opt)
            return False

        opt = Command(message, ['list'])
        if opt is not None:
            await PrivateMessage.List(user, channel, opt)
            return False

        opt = Command(message, ['info'])
        if opt is not None:
            await PrivateMessage.Info(user, channel, opt)
            return False

        opt = Command(message, ['modify'])
        if opt is not None:
            await PrivateMessage.Modify(user, channel, opt)
            return False

        opt = Command(message, ['del'])
        if opt is not None:
            await PrivateMessage.Delete(user, channel, opt)
            return False

        opt = Command(message, ['check'])
        if opt is not None:
            await PrivateMessage.Check(user, channel, opt)
            return False

        opt = Command(message, ['have'])
        if opt is not None:
            await PrivateMessage.Have(user, channel, opt)
            return False

        opt = Command(message, ['use'])
        if opt is not None:
            await PrivateMessage.Use(user, channel, opt)
            return False


# 接続に必要なオブジェクトを生成
intents = discord.Intents.default()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
intents.members = True  # membersを受け取る
client = discord.Client(intents=intents)

clanhash: Dict[int, Clan] = {}

# ギルドデータ読み込み
files = glob.glob("./clandata/*.json")

for file in files:
    clanid = int (os.path.splitext(os.path.basename(file))[0])
    if clanid != 0:
        clan = Clan.Load(clanid)
        clanhash[clanid] = clan

def GetClan(guild, message) -> Clan:
    global clanhash
    g = clanhash.get(guild.id)

    if (g is None):
        g = Clan(message.channel.id)
        clanhash[guild.id] = g

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
        Outlog(ERRFILE, '05:00 batch start len:%d ' % (len(clanhash)))
        
        for guildid, clan in clanhash.items():
            try:
                message = 'おはようございます\nメンバーの情報をリセットしました'
                resetflag = True if clan.SortieCount() != 0 else False

                if (nowdate == BATTLEPRESTART):
                    message = 'おはようございます\n明日よりクランバトルです。状況報告に名前が出ていない人は、今日中に「凸」と発言してください。'
                    clan.FullReset()
                    resetflag = True

                if (nowdate == BATTLESTART):
                    message = 'おはようございます\nいよいよクランバトルの開始です。頑張りましょう。'
                    clan.FullReset()
                    resetflag = True

                if (nowdate == BATTLEEND):
                    message = 'おはようございます\n今日がクランバトル最終日です。24時が終了時刻ですので早めに攻撃を終わらせましょう。'
                    resetflag = True

                clan.Reset()
                if resetflag:
                    clan.SetInputChannel()
                    if clan.inputchannel is not None:
                        await clan.inputchannel.send(message)
                    await Output(clan, clan.Status())
                else:
                    clan.lastmessage = None
                Clan.Save(clan, guildid)

                cstr = 'input:ok'
                if clan.inputchannel is None:
                    cstr = 'input:ng channellen: %d' % len(clan.guild.channels)

                Outlog(ERRFILE, '%s flag:%s %s' % (clan.guild.name, resetflag, cstr))
            except Exception as e:
                Outlog(ERRFILE, 'error: %s e.args:%s' % ((clan.guild.name if clan.guild is not None else 'Unknown'), e.args))

        for user in userhash.values():
            user.UsedClear()
        
        PrivateUser.SaveList(userhash)
        Outlog(ERRFILE, '05:00 batch end')

    if nowtime == '23:59':
        for clan in clanhash.values():
            if (nowdate == BATTLEEND):
                if clan.inputchannel is not None:
                    message = 'クランバトル終了です。お疲れさまでした。'
                    await clan.inputchannel.send(message)
    
    shtime = now
    for clan in clanhash.values():
        for member in clan.members.values():
            if (member.reportlimit is not None and member.reportlimit < shtime):
                member.reportlimit = None

                if clan.inputchannel is not None:
                    message = '%s 凸結果の報告をお願いします' % member.mention
                    await clan.inputchannel.send(message)


def IsClanBattle():
    return False


# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')
    Outlog(ERRFILE, "login.")

    global clanhash
    global userhash

    for guildid, clan in clanhash.items():
        if clan.guild is None:
            matchguild = [g for g in client.guilds if g.id == guildid]
            if len(matchguild) == 1:
                clan.guild = matchguild[0]
                print(matchguild[0].name + " set.")
            else: 
                print('[%d] not found' % guildid)

    for user in userhash.values():
        if user.clan is None and user.guildid != 0:
            user.clan = clanhash.get(user.guildid)
            if user.clan is None:
                print('[%d] not found' % user.guildid)
                user.guildid = 0

async def VolatilityMessage(channel, mes, time):
    log = await channel.send(mes)
    await asyncio.sleep(time)
    await log.delete()

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    if message.channel.type == discord.ChannelType.text:
        clan = GetClan(message.guild, message)
        result = await clan.on_message(message)

        if result:
            clan.Save(clan, message.guild.id)
            await Output(clan, clan.Status())
        return

    global userhash
    if message.channel.type == discord.ChannelType.private:
        user = userhash.get(message.author.id)
        if user is None:
            user = PrivateUser(message.channel, message.author)
            userhash[message.author.id] = user
        else:
            user.channel = message.channel
            user.author = message.author
        
        result = await PrivateMessage.on_message(user, message.channel, message.content)

        if result:
            pass 
        return

@client.event
async def on_raw_message_delete(payload):
    clan = clanhash.get(payload.guild_id)

    if clan is not None and clan.IsInput(payload.channel_id):

        result = await clan.on_raw_message_delete(payload)
        if result:
            clan.Save(clan, payload.guild_id)
            await Output(clan, clan.Status())

@client.event
async def on_raw_reaction_add(payload):
    clan = clanhash.get(payload.guild_id)

    if clan is not None:
        result = await clan.on_raw_reaction_add(payload)
        if result:
            clan.Save(clan, payload.guild_id)
            await Output(clan, clan.Status())

@client.event
async def on_raw_reaction_remove(payload):

    clan = clanhash.get(payload.guild_id)

    if clan is not None and clan.IsInput(payload.channel_id):

        result = await clan.on_raw_reaction_remove(payload)
        if result:
            clan.Save(clan, payload.guild_id)
            await Output(clan, clan.Status())

@client.event
async def on_member_remove(member):
    if member.bot: return

    clan = clanhash.get(member.guild.id)
    if (clan is None): return

    if member.id in clan.members:
        del clan.members[member.id]
        clan.Save(clan, member.guild.id)
        await Output(clan, clan.Status())

@client.event
async def on_guild_join(guild):
    Outlog(ERRFILE, "on_guild_join. %s" % guild.name)

@client.event
async def on_guild_remove(guild):
    global clanhash

    if guild.id in clanhash:
        del clanhash[guild.id]
        try:
            os.remove('clandata/%d.json' % (guild.id))
        except FileNotFoundError:
            pass

async def Output(clan : Clan, message : str):
    clan.SetOutputChannel()
    if clan.outputchannel is not None:
        if clan.outputlock == 1: return
        try:
            while clan.outputlock != 0:
                await asyncio.sleep(1)

            if clan.lastmessage is not None:
                clan.outputlock = 1
                try:
                    await clan.lastmessage.delete()
                except (discord.errors.NotFound, discord.errors.Forbidden):
                    pass
                clan.lastmessage = None

            try:
                clan.outputlock = 2
                clan.lastmessage = await clan.outputchannel.send(message)
            except discord.errors.Forbidden:
                clan.outputchannel = None
        finally:
            clan.outputlock = 0


def Outlog(filename, data):
    datetime_format = datetime.datetime.now()
    datestr = datetime_format.strftime("%Y/%m/%d %H:%M:%S")  # 2017/11/12 09:55:28
    print(datestr + " " + data, file=codecs.open(filename, 'a', 'utf-8'))

GlobalStrage.Load()

#ループ処理実行
loop.start()

# Botの起動とDiscordサーバーへの接続
client.run(tokenkeycode.TOKEN)

