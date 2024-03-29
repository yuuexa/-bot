import os
from flask import Flask, request, abort
import config
from datetime import datetime, timedelta
import json
from pathlib import Path

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

app = Flask(__name__)

line_bot_api = LineBotApi(config.ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

format_dict = {
    "英コミュ": "英語コミュニケーション",
    "1": "Ⅰ",
    "一": "Ⅰ",
    "a": "A",
}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    with open('./language.json', encoding="utf-8", mode="r") as f:
        language = json.load(f)

    profile = line_bot_api.get_profile(event.source.user_id)
    if not Database.is_exist('users', 'user', f'id = "{event.source.user_id}"'):
        Database.insert_data('users', 'user', '?, ?, ?, ?, ?, ?, ?, ?, ?, ?', 'ON CONFLICT(id) DO NOTHING', (event.source.user_id, profile.display_name, profile.picture_url, 'G', datetime.now(), datetime.now(), 0, "日本語", 0, 'GENERAL'))
    event.message.text = event.message.text.replace('　', ' ')
    message = event.message.text.split(' ')[0] or event.message.text
    args = event.message.text.split(' ')

    author = Database.search_data('users', 'user', f'id = "{event.source.user_id}"')
    user_lang = author[7]
    Database.insert_data('messages', 'message', '?, ?, ?, ?, ?', '', (event.message.id, event.source.user_id, profile.display_name, event.message.text, datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")))


    if Utils.isBanned(event.source.user_id) and not Utils.hasRole(event.source.user_id, 'ADMINISTRATOR'):
        reply_message = TextSendMessage(text = language["BANNED"][user_lang])
    else:
        if message == '設定':
            settings_list = ['クラス設定', '言語設定', '通知設定']
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = setting, text = setting)) for setting in settings_list]
                user = Database.search_data('users', 'user', f'id = "{event.source.user_id}"')
                createdAt = Utils.strptime(user[4]).strftime("%Y年%m月%d日 %H:%M")
                reply_message = TextSendMessage(text = language["REGISTRATION_INFORMATION"][user_lang].format(profile.display_name, user[0], user[3], user[7], createdAt, language[f"{user[9].upper()}"][user_lang]), quick_reply=QuickReply(items=items))
            else:
                username = args[1]
                if Database.is_exist('users', 'user', f'display_name = "{username}"'):
                    user = Database.search_data('users', 'user', f'display_name = "{username}"')
                    createdAt = Utils.strptime(user[4]).strftime("%Y年%m月%d日 %H:%M")
                    reply_message = TextSendMessage(text = language["REGISTRATION_INFORMATION"][user_lang].format(user[1], user[0], user[3], user[7], createdAt, language[f"{user[9].upper()}"][user_lang]))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])

        elif message == 'クラス設定':
            group_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = group, text = f'クラス設定 {group}')) for group in group_list]
                reply_message = TextSendMessage(text = language["CLASS_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            else:
                group = args[1]
                if group in group_list:
                    Database.update_data('users', 'user', f'SET class = "{group}", updatedAt = "{datetime.now()}" WHERE id = "{event.source.user_id}"')
                    reply_message = TextSendMessage(text = language["CLASS_SETTING"][user_lang].format(group))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])

        elif message == "言語設定":
            language_list = ['日本語', 'English']
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = language, text = f'言語設定 {language}')) for language in language_list]
                reply_message = TextSendMessage(text = language["LANGUAGE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            else:
                if args[1] in language_list:
                    Database.update_data('users', 'user', f'SET language = "{args[1]}", updatedAt = "{datetime.now()}" WHERE id = "{event.source.user_id}"')
                    reply_message = TextSendMessage(text = language["LANGUAGE_SETTING"][user_lang].format(args[1]))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])

        elif message == "通知設定":
            notice_list = ['受け取る', '受け取らない']
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = notice, text = f'通知設定 {notice}')) for notice in notice_list]
                reply_message = TextSendMessage(text = language["NOTICE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            else:
                if args[1] in notice_list:
                    notice_boolean = 0
                    if args[1] == '受け取る':
                        notice_boolean = 1
                    Database.update_data('users', 'user', f'SET notice = "{notice_boolean}", updatedAt = "{datetime.now()}" WHERE id = "{event.source.user_id}"')
                    reply_message = TextSendMessage(text = language["NOTICE_SETTING"][user_lang].format(args[1]))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])

        elif message == "時間割設定":
            day_list = ["A月", "A火", "A水", "A木", "A金", "B月", "B火", "B水", "B木", "B金"]
            if args[2] in day_list and len(args) == 8:
                if not Database.is_exist('timetable', 'timetable', f'(class = "{args[1].upper()}" AND day = "{args[2].upper()}")'):
                    Database.insert_data('timetable', 'timetable', '?, ?, ?, ?, ?, ?, ?', '', (args[1].upper(), args[2].upper(), args[3], args[4], args[5], args[6], args[7]))
                    reply_message = TextSendMessage(text = language["TIMETABLE_EDITING"][user_lang].format(args[1].upper(), args[2].upper(), args[3], args[4], args[5], args[6], args[7]))
                else:
                    Database.update_data('timetable', 'timetable', f'SET first = "{args[3]}", second = "{args[4]}", third = "{args[5]}", fourth = "{args[6]}", fifth = "{args[7]}" WHERE (class = "{args[1].upper()}" AND day = "{args[2].upper()}")')
                    reply_message = TextSendMessage(text = language["TIMETABLE_EDITING"][user_lang].format(args[1].upper(), args[2].upper(), args[3], args[4], args[5], args[6], args[7]))
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('時間割設定 [クラス] [曜日] [1時間目] ...'))

        elif message == "時間割作成":
            weekday = [ '月', '火', '水', '木', '金', '土', '日' ]
            nowadays = datetime.now() + timedelta(days = 0 - datetime.now().weekday())
            after = nowadays + timedelta(days = 32)
            if Utils.hasRole(event.source.user_id, 'ADMINISTRATOR'):
                Utils.create_timetable(args[1])
                reply_message = TextMessage(text = f'{nowadays.strftime("%m月%d日")} ～ {after.strftime("%m月%d日")} の時間割を作成しました')

        elif message == "テスト作成":
            subject_list = ["数学", "生物", "化学", "物理", "英コミュ", "論理表現", "現代の国語", "言語文化"]
            if len(args) == 2:
                items = [QuickReplyButton(action = MessageAction(label = subject, text = f'テスト作成 {args[1]} {subject}')) for subject in subject_list]
                reply_message = TextSendMessage(text = language["SUBJECT_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 3:
                date_list = []
                for i in range(11):
                    date = datetime.now() + timedelta(i)
                    date_list.append(date.strftime("%m月%d日"))
                items = [QuickReplyButton(action = MessageAction(label = day, text = f'テスト作成 {args[1]} {args[2]} {day}')) for day in date_list]
                reply_message = TextSendMessage(text = language["DATE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 4:
                time_list = ['なし']
                for i in range(12):
                    time_list.append(f'{i * 2}:00')
                items = [QuickReplyButton(action = MessageAction(label = time, text = f'テスト作成 {args[1]} {args[2]} {args[3]} {time}')) for time in time_list]
                reply_message = TextSendMessage(text = language["TIME_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 5:
                time = ' '
                if not args[4] == 'なし':
                    time = args[4]
                if not Database.is_exist('tests', 'test', f'(class = "{author[3]}" AND range = "{args[1]}" AND subject = "{args[2]}" AND date = "{args[3]}" AND time = "{time}")'):
                    Database.insert_data('tests', 'test', '?, ?, ?, ?, ?, ?', '', (author[3], args[1], args[2], args[3], time, event.source.user_id))
                    reply_message = TextSendMessage(text = language["CREATION_TEST"][user_lang].format(args[1], args[2], f'{args[3]} {time}'))
                else:
                    reply_message = TextSendMessage(text = language["ALREADY_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('テスト作成 [範囲]'))

        elif message == "テスト編集":
            subject_list = ["数学", "生物", "化学", "物理", "英コミュ", "論理表現", "現代の国語", "言語文化"]
            if len(args) == 2:
                if Database.is_exist('tests', 'test', f'(class = "{author[3]}" AND range = "{args[1]}")'):
                    if Utils.isEditable(Database.search_data('tests', 'test', f'(class = "{author[3]}" AND range = "{args[1]}")')[5], event.source.user_id):
                        items = [QuickReplyButton(action = MessageAction(label = subject, text = f'テスト編集 {args[1]} {subject}')) for subject in subject_list]
                        reply_message = TextSendMessage(text = language["SUBJECT_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
                    else:
                        reply_message = TextSendMessage(text = language["UNEDITABLE"][user_lang])
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            elif len(args) == 3:
                date_list = []
                for i in range(11):
                    date = datetime.now() + timedelta(i)
                    date_list.append(date.strftime("%m月%d日"))
                items = [QuickReplyButton(action = MessageAction(label = day, text = f'テスト編集 {args[1]} {args[2]} {day}')) for day in date_list]
                reply_message = TextSendMessage(text = language["DATE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 4:
                time_list = ['なし']
                for i in range(12):
                    time_list.append(f'{i * 2}:00')
                items = [QuickReplyButton(action = MessageAction(label = time, text = f'テスト編集 {args[1]} {args[2]} {args[3]} {time}')) for time in time_list]
                reply_message = TextSendMessage(text = language["TIME_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 5:
                time = ' '
                if not args[4] == 'なし':
                    time = args[4]
                if Database.is_exist('tests', 'test', f'(class = "{author[3]}" AND range = "{args[1]}")'):
                    Database.update_data('tests', 'test', f'SET subject = "{args[2]}", date = "{args[3]}", time = "{time}" WHERE (class = "{author[3]}" AND range = "{args[1]}")')
                    reply_message = TextSendMessage(text = language["UPDATE_TEST"][user_lang].format(args[1], args[2], f'{args[3]} {time}'))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('テスト編集 [範囲]'))

        elif message == "テスト削除":
            if len(args) == 1:
                if Database.is_exist('tests', 'test', f'(class = "{author[3]}" AND range = "{args[1]}")'):
                    if Utils.isEditable(Database.search_data('tests', 'test', f'(class = "{author[3]}" AND range = "{args[1]}")')[5], event.source.user_id):
                        Database.delete_data('tests', 'test', f'(class = "{author[3]}" AND range = "{args[1]}")')
                        reply_message = TextSendMessage(text = language["DELETE_TASK"][user_lang].format(args[1]))
                    else:
                        reply_message = TextSendMessage(text = language["UNEDITABLE"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('課題編集 [課題名]'))

        elif message == "課題作成":
            subject_list = ["情報", "数学", "生物", "化学", "物理", "地理総合", "公共", "英コミュ", "論理表現", "現代の国語", "言語文化", "体育"]
            if len(args) == 2:
                items = [QuickReplyButton(action = MessageAction(label = subject, text = f'課題作成 {args[1]} {subject}')) for subject in subject_list]
                reply_message = TextSendMessage(text = language["SUBJECT_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 3 and args[2] in subject_list:
                date_list = []
                for i in range(11):
                    date = datetime.now() + timedelta(i)
                    date_list.append(date.strftime("%m月%d日"))
                items = [QuickReplyButton(action = MessageAction(label = day, text = f'課題作成 {args[1]} {args[2]} {day}')) for day in date_list]
                reply_message = TextSendMessage(text = language["DATE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 4 and args[2] in subject_list:
                time_list = ['なし']
                for i in range(12):
                    time_list.append(f'{i * 2}:00')
                items = [QuickReplyButton(action = MessageAction(label = time, text = f'課題作成 {args[1]} {args[2]} {args[3]} {time}')) for time in time_list]
                reply_message = TextSendMessage(text = language["TIME_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 5 and args[2] in subject_list:
                time = ' '
                if not args[4] == 'なし':
                    time = args[4]
                if not Database.is_exist('tasks', 'task', f'(class = "{author[3]}" AND name = "{args[1]}" AND subject = "{args[2]}" AND date = "{args[3]}" AND time = "{time}")'):
                    Database.insert_data('tasks', 'task', '?, ?, ?, ?, ?, ?', '', (author[3], args[1], args[2], args[3], time, event.source.user_id))
                    reply_message = TextSendMessage(text = language["CREATION_TASK"][user_lang].format(args[1], args[2], f'{args[3]} {time}'))
                else:
                    reply_message = TextSendMessage(text = language["ALREADY_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('課題作成 [課題名]'))

        elif message == "課題編集":
            subject_list = ["情報", "数学", "生物", "化学", "物理", "地理総合", "公共", "英コミュ", "論理表現", "現代の国語", "言語文化", "体育"]
            if len(args) == 2:
                if Database.is_exist('tasks', 'task', f'(class = "{author[3]}" AND name = "{args[1]}")'):
                    if Utils.isEditable(Database.search_data('tasks', 'task', f'(class = "{author[3]}" AND name = "{args[1]}")')[5], event.source.user_id):
                        items = [QuickReplyButton(action = MessageAction(label = subject, text = f'課題編集 {args[1]} {subject}')) for subject in subject_list]
                        reply_message = TextSendMessage(text = language["SUBJECT_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
                    else:
                        reply_message = TextSendMessage(text = language["UNEDITABLE"][user_lang])
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            elif len(args) == 3 and args[2] in subject_list:
                date_list = []
                for i in range(11):
                    date = datetime.now() + timedelta(i)
                    date_list.append(date.strftime("%m月%d日"))
                items = [QuickReplyButton(action = MessageAction(label = day, text = f'課題編集 {args[1]} {args[2]} {day}')) for day in date_list]
                reply_message = TextSendMessage(text = language["DATE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 4 and args[2] in subject_list:
                time_list = ['なし']
                for i in range(12):
                    time_list.append(f'{i * 2}:00')
                items = [QuickReplyButton(action = MessageAction(label = time, text = f'課題編集 {args[1]} {args[2]} {args[3]} {time}')) for time in time_list]
                reply_message = TextSendMessage(text = language["TIME_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 5 and args[2] in subject_list:
                time = ' '
                if not args[4] == 'なし':
                    time = args[4]
                if Database.is_exist('tasks', 'task', f'(class = "{author[3]}" AND name = "{args[1]}")'):
                    Database.update_data('tasks', 'task', f'SET subject = "{args[2]}", date = "{args[3]}", time = "{time}" WHERE (class = "{author[3]}" AND name = "{args[1]}")')
                    reply_message = TextSendMessage(text = language["UPDATE_TASK"][user_lang].format(args[1], args[2], f'{args[3]} {time}'))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('課題編集 [課題名]'))

        elif message == "課題削除":
            if len(args) == 1:
                if Database.is_exist('tasks', 'task', f'(class = "{author[3]}" AND name = "{args[1]}")'):
                    if Utils.isEditable(Database.search_data('tasks', 'task', f'(class = "{author[3]}" AND name = "{args[1]}")')[5], event.source.user_id):
                        Database.delete_data('tasks', 'task', f'(class = "{author[3]}" AND name = "{args[1]}")')
                        reply_message = TextSendMessage(text = language["DELETE_TASK"][user_lang].format(args[1]))
                    else:
                        reply_message = TextSendMessage(text = language["UNEDITABLE"][user_lang])
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('課題編集 [課題名]'))

        elif message == "禁止":
            if len(args) == 2:
                if Database.is_exist('users', 'user', f'(id = "{args[1]}" OR display_name = "{args[1]}")'):
                    Database.update_data('users', 'user', f'SET banned = "1", updatedAt = "{datetime.now()}" WHERE (id = "{args[1]}" OR display_name = "{args[1]}")')
                    user = Database.search_data('users', 'user', f'(id = "{args[1]}" OR display_name = "{args[1]}")')
                    reply_message = TextSendMessage(text = language["BAN_USER"][user_lang].format(user[1]))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('禁止 [ユーザーID または ユーザーネーム]'))

        elif message == "解除":
            if len(args) == 2:
                if Database.is_exist('users', 'user', f'(id = "{args[1]}" OR display_name = "{args[1]}")'):
                    Database.update_data('users', 'user', f'SET banned = "0" WHERE (id = "{args[1]}" AND display_name = "{args[1]}")')
                    reply_message = TextSendMessage(text = language["UNBAN_USER"][user_lang].format(Database.search_data('users', 'user', f'WHERE (id = "{args[1]}" AND display_name = "{args[1]}")')[2]))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('解除 [ユーザーID または ユーザーネーム]'))

        elif message == "告知作成":
            news_type_list = ["授業変更", "係・委員会", "告知"]
            if len(args) == 2:
                items = [QuickReplyButton(action = MessageAction(label = news_type, text = f'告知作成 {args[1]} {news_type}')) for news_type in news_type_list]
                reply_message = TextSendMessage(text = language["TYPE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 3 and args[2] in news_type_list:
                date_list = []
                for i in range(11):
                    date = datetime.now() + timedelta(i)
                    date_list.append(date.strftime("%m月%d日"))
                items = [QuickReplyButton(action = MessageAction(label = day, text = f'告知作成 {args[1]} {args[2]} {day}')) for day in date_list]
                reply_message = TextSendMessage(text = language["DATE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 4 and args[2] in news_type_list:
                time_list = ['なし']
                for i in range(12):
                    time_list.append(f'{i * 2}:00')
                items = [QuickReplyButton(action = MessageAction(label = time, text = f'告知作成 {args[1]} {args[2]} {args[3]} {time}')) for time in time_list]
                reply_message = TextSendMessage(text = language["TIME_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 5 and args[2] in news_type_list:
                time = ' '
                if not args[4] == 'なし':
                    time = args[4]
                if not Database.is_exist('news', 'news', f'(class = "{author[3]}" AND name = "{args[1]}" AND type = "{args[2]}" AND date = "{args[3]}" AND time = "{time}")'):
                    Database.insert_data('news', 'news', '?, ?, ?, ?, ?, ?', '', (author[3], args[1], args[2], args[3], time, event.source.user_id))
                    reply_message = TextSendMessage(text = language["CREATION_NEWS"][user_lang].format(args[1], args[2], f'{args[3]} {time}'))
                else:
                    reply_message = TextSendMessage(text = language["ALREADY_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('告知作成 [告知名]'))

        elif message == "告知編集":
            news_type_list = ["授業変更", "係・委員会", "告知"]
            if len(args) == 2:
                if Database.is_exist('news', 'news', f'(class = "{author[3]}" AND name = "{args[1]}")'):
                    if Utils.isEditable(Database.search_data('news', 'news', f'(class = "{author[3]}" AND name = "{args[1]}")')[5], event.source.user_id):
                        items = [QuickReplyButton(action = MessageAction(label = news_type, text = f'告知編集 {args[1]} {news_type}')) for news_type in news_type_list]
                        reply_message = TextSendMessage(text = language["TYPE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
                    else:
                        reply_message = TextSendMessage(text = language["UNEDITABLE"][user_lang])
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            elif len(args) == 3 and args[2] in news_type_list:
                date_list = []
                for i in range(11):
                    date = datetime.now() + timedelta(i)
                    date_list.append(date.strftime("%m月%d日"))
                items = [QuickReplyButton(action = MessageAction(label = day, text = f'告知編集 {args[1]} {args[2]} {day}')) for day in date_list]
                reply_message = TextSendMessage(text = language["DATE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 4 and args[2] in news_type_list:
                time_list = ['なし']
                for i in range(12):
                    time_list.append(f'{i * 2}:00')
                items = [QuickReplyButton(action = MessageAction(label = time, text = f'告知編集 {args[1]} {args[2]} {args[3]} {time}')) for time in time_list]
                reply_message = TextSendMessage(text = language["TIME_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 5 and args[2] in news_type_list:
                time = ' '
                if not args[4] == 'なし':
                    time = args[4]
                if Database.is_exist('news', 'news', f'(class = "{author[3]}" AND name = "{args[1]}")'):
                    Database.update_data('news', 'news', f'SET type = "{args[2]}", date = "{args[3]}", time = "{time}" WHERE (class = "{author[3]}" AND name = "{args[1]}")')
                    reply_message = TextSendMessage(text = language["UPDATE_NEWS"][user_lang].format(args[1], args[2], f'{args[3]} {time}'))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('告知編集 [告知名]'))

        elif message == "告知削除":
            if len(args) == 1:
                if Database.is_exist('news', 'news', f'(class = "{author[3]}" AND name = "{args[1]}")'):
                    if Utils.isEditable(Database.search_data('news', 'news', f'(class = "{author[3]}" AND name = "{args[1]}")')[5], event.source.user_id):
                        Database.delete_data('news', 'news', f'(class = "{author[3]}" AND name = "{args[1]}")')
                        reply_message = TextSendMessage(text = language["DELETE_NEWS"][user_lang].format(args[1]))
                    else:
                        reply_message = TextSendMessage(text = language["UNEDITABLE"][user_lang])
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('告知削除 [告知名]'))

        elif message == "役割編集":
            role_list = ['General', 'Editor', 'Administrator']
            if Utils.hasRole(event.source.user_id, 'ADMINISTRATOR'):
                if Database.is_exist('users', 'user', f'(id = "{args[1]}" OR display_name = "{args[1]}")'):
                    if len(args) == 1:
                        reply_message = TextSendMessage(text = language["INVALID_ARGUMENT"][user_lang].format('[役割編集] [ユーザーID もしくは ユーザー名]'))
                    if len(args) == 2:
                        items = [QuickReplyButton(action = MessageAction(label = role, text = f'役割編集 {args[1]} {role}')) for role in role_list]
                        reply_message = TextSendMessage(text = language["ROLE_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
                    if len(args) == 3:
                        user = Database.search_data('users', 'user', f'(id = "{args[1]}" OR display_name = "{args[1]}")')
                        Database.update_data('users', 'user', f'SET roles = "{args[2].upper()}", updatedAt = "{datetime.now()}" WHERE (id = "{args[1]}" OR display_name = "{args[1]}")')
                        reply_message = TextSendMessage(text = language["ROLE_EDIT"][user_lang].format(args[1], language[f"{args[2].upper()}"][user_lang]))
                        line_bot_api.push_message(user[0], messages = TextSendMessage(text = language["ROLE_EDITED"][user_lang].format(language[f"{args[2].upper()}"][user_lang])))
                else:
                    reply_message = TextSendMessage(text = language["NOT_EXIST"][user_lang])
            else:
                reply_message = TextSendMessage(text = language["ADMIN_COMMAND"][user_lang])

        elif message == "教科検索":
            subject_list = ["数学Ⅰ", "数学A", "ヴェリタスⅠ", "エンジニアリング", "S.E.B(生物)", "S.E.C(化学)", "S.E.P(物理)", "英語コミュニケーション", "音楽Ⅰ", "美術Ⅰ", "H.R."]
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = subject, text = f'教科検索 {subject}')) for subject in subject_list]
                reply_message = TextSendMessage(text = language["SUBJECT_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            elif len(args) == 2:
                args[1] = Utils.format_text(args[1].upper())
                results = Database.filter_data('timetable', 'timetable', f'(class = "{author[3]}") AND (first = "{args[1]}" OR second = "{args[1]}" OR third = "{args[1]}" OR fourth = "{args[1]}" OR fifth = "{args[1]}")')
                schedule = []
                for i in range(len(results)):
                    schedule.append(f'{results[i][1]} - {language["TIMETABLE_PERIOD"][user_lang].format(results[i].index(args[1]) - 1)}')
                reply_message = TextSendMessage(text = language["TIMETABLE_SEARCH"][user_lang].format(args[1], '\n'.join(schedule) or language["NONE"][user_lang]))

        elif message == '時間割':
            day_list = ["今日", "明日", "A月", "A火", "A水", "A木", "A金", "B月", "B火", "B水", "B木", "B金"]
            items = [QuickReplyButton(action = MessageAction(label = f"{day}", text = f"{day}曜日の時間割")) for day in day_list]
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = day, text = f'時間割 {day}')) for day in day_list]
                reply_message = TextSendMessage(text = language["TIMETABLE_DAY"][user_lang], quick_reply=QuickReply(items=items))
            elif args[1] in day_list:
                if args[1] == '今日' or args[1] == '明日':
                    date = datetime.now()
                    if args[1] == '明日':
                        date = datetime.now() + timedelta(1)
                    if Database.is_exist('schedule', 'schedule', f'(class = "{author[3]}" AND day = "{date.strftime("%m月%d日")}")'):
                        timetable = Database.search_data('schedule', 'schedule', f'(class = "{author[3]}" AND day = "{date.strftime("%m月%d日")}")')
                        reply_message = TextSendMessage(text = language["TIMETABLE"][user_lang].format(author[3], f'{args[1]}({date.strftime("%m月%d日")})', timetable[2], timetable[3], timetable[4], timetable[5], timetable[6]))
                elif Database.is_exist('timetable', 'timetable', f'(class = "{author[3]}" AND day = "{event.message.text.split(" ")[1]}")'):
                    timetable = Database.search_data('timetable', 'timetable', f'(class = "{author[3]}" AND day = "{event.message.text.split(" ")[1]}")')
                    reply_message = TextSendMessage(text = language["TIMETABLE"][user_lang].format(timetable[0], timetable[1], timetable[2], timetable[3], timetable[4], timetable[5], timetable[6]))
                else:
                    reply_message = TextSendMessage(text = language["TIMETABLE_EDIT"][user_lang])

        elif message == 'テスト範囲':
            subject_list = ["今日", "明日", "数学", "生物", "化学", "物理", "英コミュ", "論理表現", "現代の国語", "言語文化"]
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = subject, text = f'テスト範囲 {subject}')) for subject in subject_list]
                reply_message = TextSendMessage(text = language["SUBJECT_SELECTION"][user_lang], quick_reply=QuickReply(items=items))
            else:
                nowadays = datetime.now()
                tomorrow = nowadays + timedelta(1)
                after = nowadays + timedelta(10)
                tests = []
                if args[1] == "今日" or args[1] == "明日":
                    date = nowadays
                    if args[1] == "明日":
                        date = tomorrow
                    for i in Database.filter_data('tests', 'test', f'(class = "{author[3]}" AND date = "{date.strftime("%m月%d日")}") ORDER BY time, range ASC'):
                        if i[4] == ' ':
                            tests.append(f'⧼ {i[2]} ⧽\n«範囲» {i[1]}')
                        else:
                            tests.append(f'⧼ {i[2]} ⧽\n«範囲» {i[1]}\n«日時» ～{i[4]}')

                    reply_message = TextSendMessage(text = language["TESTS"][user_lang].format(date.strftime("%m月%d日"), '\n\n'.join(tests) or language["NONE"][user_lang]))
                else:
                    for i in Database.filter_data('tests', 'test', f'(class = "{author[3]}" AND subject = "{args[1]}" AND "{nowadays.strftime("%m月%d日")}" <= date <= "{after.strftime("%m月%d日")}") ORDER BY date, time, range ASC'):
                        if i[4] == ' ':
                            tests.append(f'⧼ {i[1]} ⧽\n«日時» {i[3]}')
                        else:
                            tests.append(f'⧼ {i[1]} ⧽\n«日時» {i[3]} ～{i[4]}')
                    reply_message = TextSendMessage(text = language["TESTS"][user_lang].format(f'{nowadays.strftime("%m月%d日")} - {after.strftime("%m月%d日")}', '\n\n'.join(tests) or language["NONE"][user_lang]))

        elif message == '課題':
            nowadays = datetime.now()
            after = nowadays + timedelta(10)
            tasks = []
            for i in Database.filter_data('tasks', 'task', f'(class = "{author[3]}" AND "{nowadays.strftime("%m月%d日")}" <= date AND date <= "{after.strftime("%m月%d日")}") ORDER BY date, time, name ASC'):
                if i[4] == ' ':
                    tasks.append(f'⧼ {i[1]} ⧽\n«教科» {i[2]}\n«提出日時» {i[3]}')
                else:
                    tasks.append(f'⧼ {i[1]} ⧽\n«教科» {i[2]}\n«提出日時» {i[3]} ～{i[4]}')
            reply_message = TextSendMessage(text = language["TASKS"][user_lang].format(f'{nowadays.strftime("%m月%d日")} - {after.strftime("%m月%d日")}', '\n\n'.join(tasks) or language["NONE"][user_lang]))

        elif message == '告知':
            nowadays = datetime.now()
            after = nowadays + timedelta(10)
            news = []
            for i in Database.filter_data('news', 'news', f'(class = "{author[3]}" AND "{nowadays.strftime("%m月%d日")}" <= date AND date <= "{after.strftime("%m月%d日")}") ORDER BY date, time, name ASC'):
                if i[4] == ' ':
                    news.append(f'⧼ {i[1]} ⧽\n«種類» {i[2]}\n«日時» {i[3]}')
                else:
                    news.append(f'⧼ {i[1]} ⧽\n«種類» {i[2]}\n«日時» {i[3]} ～{i[4]}')
            reply_message = TextSendMessage(text = language["NEWS"][user_lang].format(f'{nowadays.strftime("%m月%d日")} - {after.strftime("%m月%d日")}', '\n\n'.join(news) or language["NONE"][user_lang]))

        elif message == '予定':
            schedule_list = ['昨日', '今日', '明日']
            if len(args) == 1:
                items = [QuickReplyButton(action = MessageAction(label = schedule, text = f'予定 {schedule}')) for schedule in schedule_list]
                reply_message = TextSendMessage(text = '表示する種類を選択してください', quick_reply=QuickReply(items=items))
            else:
                nowadays = datetime.now()
                yesterday = nowadays - timedelta(1)
                tomorrow = nowadays + timedelta(1)
                if args[1] == '昨日':
                    date = yesterday
                elif args[1] == '今日':
                    date = nowadays
                elif args[1] == '明日':
                    date = tomorrow
                if Database.is_exist('schedule', 'schedule', f'(day = "{date.strftime("%m月%d日")}" AND class = "{author[3]}")'):
                    timetable = Database.search_data('schedule', 'schedule', f'(day = "{date.strftime("%m月%d日")}" AND class = "{author[3]}")')
                    reply_message = TextSendMessage(text = language["SCHEDULE_FULL"][user_lang].format(f'{event.message.text.split(" ")[1]}({date.strftime("%m月%d日")})', timetable[2], timetable[3], timetable[4], timetable[5], timetable[6], '\n'.join(Utils.get_tests(author[3], date.strftime("%m月%d日"))) or language["NONE"][user_lang], '\n'.join(Utils.get_tasks(author[3], date.strftime("%m月%d日"))) or language["NONE"][user_lang], '\n'.join(Utils.get_news(author[3], date.strftime("%m月%d日"))) or language["NONE"][user_lang]))
                else:
                    tasks = []
                    news = []
                    tests = []

                    for i in Database.filter_data('tests', 'test', f'(class = "{author[3]}" AND date = "{date.strftime("%m月%d日")}")'):
                        if i[4] == ' ':
                            tests.append(f'⟦{i[2]}⟧ {i[1]}')
                        else:
                            tests.append(f'⟦{i[2]}⟧ {i[1]} ～{i[4]}')
                    for i in Database.filter_data('tasks', 'task', f'(class = "{author[3]}" AND date = "{date.strftime("%m月%d日")}")'):
                        if i[4] == ' ':
                            tasks.append(f'⟦{i[2]}⟧ {i[1]}')
                        else:
                            tasks.append(f'⟦{i[2]}⟧ {i[1]} ～{i[4]}')
                    for i in Database.filter_data('news', 'news', f'(class = "{author[3]}" AND date = "{date.strftime("%m月%d日")}")'):
                        if i[4] == ' ':
                            news.append(f'⟦{i[2]}⟧ {i[1]}')
                        else:
                            news.append(f'⟦{i[2]}⟧ {i[1]} ～{i[4]}')

                    reply_message = TextSendMessage(text = language["SCHEDULE"][user_lang].format(f'{event.message.text.split(" ")[1]}({date.strftime("%m月%d日")})', '\n'.join(tasks) or language["NONE"][user_lang], '\n'.join(tests) or language["NONE"][user_lang], '\n'.join(news) or language["NONE"][user_lang]))
        elif message == 'ヘルプ':
            reply_message = TextSendMessage(text = language["HELP"][user_lang])
        else:
            reply_message = TextSendMessage(text = event.message.text)

    line_bot_api.reply_message(
        event.reply_token,
        reply_message
    )

@handler.add(MessageEvent, message=(ImageMessage, AudioMessage))
def handle_image_audio_message(event):
    content = line_bot_api.get_message_content(event.message.id)
    if not os.path.isdir(f'./storage/{event.source.user_id}'):
        os.makedirs(f'./storage/{event.source.user_id}')
    with open(Path(f'./storage/{event.source.user_id}/{event.message.id}.jpg'), 'wb') as f:
        for c in content.iter_content():
            f.write(c)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text = str(ImageData.image_to_text(f'storage/{event.source.user_id}/{event.message.id}.jpg', 'jpn')))
    )

if __name__ == "__main__":
    #Database
    Database.create_table('users', 'user', 'id primary key, display_name, avatar, class, createdAt none, updatedAt none, banned, language, notice, roles')
    Database.create_table('schedule', 'schedule', 'day, class, first, second, third, fourth, fifth, tests, tasks, news, notice')
    Database.create_table('timetable', 'timetable', 'class, day, first, second, third, fourth, fifth')
    Database.create_table('messages', 'message', 'message_id, user_id, username, content, date')
    Database.create_table('admins', 'admin', 'id primary key, display_name, class, createdAt none')
    Database.create_table('tests', 'test', 'class, range, subject, date, time, author')
    Database.create_table('tasks', 'task', 'class, name, subject, date, time, author')
    Database.create_table('news', 'news', 'class, name, type, date, time, author')
    Database.create_table('temp', 'temp', 'id primary key, data')

    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)