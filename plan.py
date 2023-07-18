import os
from flask import Flask, request, abort
import config
from datetime import datetime, timedelta
from pathlib import Path
import schedule
from time import sleep
import json

#自作クラスの読み込み
import Database
import Utils
import ImageData
Database = Database.Database()
Utils = Utils.Utils()
ImageData = ImageData.ImageData()

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, AudioMessage, QuickReplyButton, MessageAction, QuickReply, FlexSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn
)

line_bot_api = LineBotApi(config.ACCESS_TOKEN)

def plan(group, day, user_lang):
    with open('./language.json', encoding="utf-8", mode="r") as f:
        language = json.load(f)

    nowadays = datetime.now()
    tomorrow = nowadays + timedelta(1)
    if day == '今日':
        date = nowadays
    elif day == '明日':
        date = tomorrow

    timetable = Database.search_data('schedule', 'schedule', f'(day = "{date.strftime("%m月%d日")}" AND class = "{group}")')
    return TextSendMessage(text = language["SCHEDULE_FULL"][user_lang].format(f'{day}({date.strftime("%m月%d日")})', timetable[2], timetable[3], timetable[4], timetable[5], timetable[6], '\n'.join(Utils.get_tests(group, date.strftime("%m月%d日"))) or language["NONE"][user_lang], '\n'.join(Utils.get_tasks(group, date.strftime("%m月%d日"))) or language["NONE"][user_lang], '\n'.join(Utils.get_news(group, date.strftime("%m月%d日"))) or language["NONE"][user_lang]))

def tomorrow():
    for user in Database.fetch_all('users', 'user'):
        if Database.is_exist('schedule', 'schedule', f'(class = "{user[3]}" AND day = "{(datetime.now() + timedelta(1)).strftime("%m月%d日")}")'):
            notice = Database.search_data('schedule', 'schedule', f'(class = "{user[3]}" AND day = "{(datetime.now() + timedelta(1)).strftime("%m月%d日")}")')
            if (user[8] == '1') and (notice[10] == '1'):
                line_bot_api.push_message(user[0], messages = plan(user[3], '明日', user[7]))
                print(f'{user[1]} に TOMORROW を送信')

def today():
    for user in Database.fetch_all('users', 'user'):
        if Database.is_exist('schedule', 'schedule', f'(class = "{user[3]}" AND day = "{datetime.now().strftime("%m月%d日")}")'):
            notice = Database.search_data('schedule', 'schedule', f'(class = "{user[3]}" AND day = "{datetime.now().strftime("%m月%d日")}")')
            if (user[8] == '1') and (notice[10] == '1'):
                line_bot_api.push_message(user[0], messages = plan(user[3], '今日', user[7]))
                print(f'{user[1]} に TODAY を送信')

def send_message():
    weeks = [ 'A', 'B', '作成しない' ]
    items = [QuickReplyButton(action = MessageAction(label = week, text = f'時間割作成 {week}')) for week in weeks]
    for user in Database.filter_data('users', 'user', f'roles = "ADMINISTRATOR"'):
        line_bot_api.push_message(user[0], messages = TextSendMessage(text = '1か月分の時間割を作成します。\n今週はA・Bどちらの週ですか？', quick_reply=QuickReply(items=items)))

schedule.every().days.at("07:00").do(today)
schedule.every().days.at("21:00").do(tomorrow)
schedule.every(1).weeks.do(send_message)

while True:
    schedule.run_pending()
    sleep(1)