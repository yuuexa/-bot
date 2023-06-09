from flask import Flask, request, abort
import sqlite3
import datetime

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReplyButton, MessageAction, QuickReply, FlexSendMessage
)

app = Flask(__name__)

line_bot_api = LineBotApi('RHR3qFBblPn555EsSqZw1r6Kig44qise/QjlhTzW8uadAYYxdorNZ0w+V3jQf0ntys71+nDx64ta6q1Qe2j10vgmFk5Jg4imxxmcVr4HXN6tKgjMEBA/8LwGLisuMX3JpWESWOqSKVEhKQDOF3sMSgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('cfb1c2b56cca2a106552842d5a531863')

lesson = {
    "A月曜日の時間割": ["エンジニアリング", "数学A", "S.E.B(生物)", "地理総合", "H.R."],
    "A火曜日の時間割": ["音楽", "現代の国語", "英語コミュニケーション", "数学A", "S.E.C(化学)"],
    "A水曜日の時間割": ["体育", "S.E.C(化学)", "言語文化", "数学Ⅰ", "ヴェリタスⅠ"],
    "A木曜日の時間割": ["言語文化", "公共", "数学Ⅰ", "現代の国語", "英語コミュニケーション"],
    "A金曜日の時間割": ["地理総合", "数学Ⅰ", "S.E.P(物理)", "論理表現", "保健"],
    "B月曜日の時間割": ["公共", "言語文化", "S.E.B(生物)", "数学Ⅰ", "H.R."],
    "B火曜日の時間割": ["英語コミュニケーション", "音楽", "体育", "数学A", "現代の国語"],
    "B水曜日の時間割": ["数学Ⅰ", "英語コミュニケーション", "エンジニアリング", "S.E.P(物理)", "論理表現"],
    "B木曜日の時間割": ["公共", "論理表現", "数学Ⅰ", "S.E.C(化学)", "S.E.B(生物)"],
    "B金曜日の時間割": ["地理総合", "体育", "S.E.P(物理)", "保健", "音楽"],
}

admin = {
    "課題追加": "[課題名] [教科] [期限]",
    "課題作成": "[課題名] [教科] [期限]",
    "課題削除": "[課題ID]",
    "お知らせ追加": "[種類] [内容] [日付]",
    "お知らせ作成": "[種類] [内容] [日付]",
    "お知らせ削除": "[お知らせID]",
    "テスト追加": "[範囲] [教科] [日付]",
    "テスト作成": "[範囲] [教科] [日付]",
    "テスト削除": "[テストID]",
}

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def fetch_data(database_name, table_name):
    conn = sqlite3.connect(f'{database_name}.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    date = 'date'
    if database_name == 'messages':
        table_name = 'message'
    elif database_name == 'term_tests':
        table_name = 'tests'
    if database_name == 'term_tests':
        date = 'subject'
    elif database_name == 'tasks':
        date = 'deadline'
    cursor.execute(f'SELECT * FROM {table_name} ORDER BY "{date}" DESC LIMIT 30')
    result = [dict(row) for row in cursor.fetchall()]
    return result

def message(event):
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS message(id, display_name, message, date)"""
    cursor.execute(sql)
    conn.commit()

    sql = """INSERT INTO message VALUES(?, ?, ?, ?)"""

    profile = line_bot_api.get_profile(event.source.user_id)
    data = ((event.source.user_id, profile.display_name, event.message.text, datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')))#挿入するレコードを指定
    cursor.execute(sql, data)
    conn.commit()

def users(event):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS users(id primary key, display_name, avatar, banned, date)"""
    cursor.execute(sql)
    conn.commit()

    sql = """INSERT INTO users VALUES(?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING;"""

    profile = line_bot_api.get_profile(event.source.user_id)
    data = ((event.source.user_id, profile.display_name, profile.picture_url, 0, datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')))#挿入するレコードを指定
    cursor.execute(sql, data)
    conn.commit()

def find_user(user):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS users(id primary key, display_name, avatar, banned, date)"""
    cursor.execute(sql)
    conn.commit()

    sql = f"""SELECT * FROM users WHERE display_name = "{user}";"""

    cursor.execute(sql)
    conn.commit()

    user = cursor.fetchone()
    return user

def isAdmin(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS users(id primary key, display_name, avatar, banned, date)"""
    cursor.execute(sql)
    conn.commit()

    sql = f"""SELECT * FROM users WHERE id = "{user_id}";"""

    cursor.execute(sql)
    conn.commit()

    user = cursor.fetchone()
    if user[0] == 'Ud713d7bf56b49d0f40c0712335f625ba':
        user = True
    else:
        user = False
    return user

def banned_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS users(id primary key, display_name, avatar, banned, date)"""
    cursor.execute(sql)
    conn.commit()

    sql = f"""SELECT * FROM users WHERE id = "{user_id}";"""

    cursor.execute(sql)
    conn.commit()

    user = cursor.fetchone()
    if user[3] == 1:
        user = True
    else:
        user = False
    return user

def ban_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS users(id primary key, display_name, avatar, banned, date)"""
    cursor.execute(sql)
    conn.commit()

    sql = f"""UPDATE users SET banned = 1 WHERE id = "{user_id}";"""

    cursor.execute(sql)
    conn.commit()

def unban_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS users(id primary key, display_name, avatar, banned, date)"""
    cursor.execute(sql)
    conn.commit()

    sql = f"""UPDATE users SET banned = 0 WHERE id = "{user_id}";"""

    cursor.execute(sql)
    conn.commit()

# 課題関連
def add_task(event, task_name, task_subject, task_deadline):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS tasks(name, subject, deadline, author, id)"""
    cursor.execute(sql)
    conn.commit()

    sql = """INSERT INTO tasks VALUES(?, ?, ?, ?, ?)"""

    profile = line_bot_api.get_profile(event.source.user_id)
    data = ((task_name, task_subject, task_deadline, profile.display_name, event.message.id))#挿入するレコードを指定
    cursor.execute(sql, data)
    conn.commit()

def remove_task(id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS tasks(name, subject, deadline, author, id)"""
    cursor.execute(sql)
    conn.commit()

    cursor.execute(f"DELETE FROM tasks WHERE id = '{id}'")
    conn.commit()

def show_tasks():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS tasks(name, subject, deadline, author, id)"""
    cursor.execute(sql)
    conn.commit()

    after = datetime.date.today() + datetime.timedelta(days=10)
    cursor.execute(f'SELECT * FROM tasks WHERE (deadline >= "{datetime.date.today().strftime("%m-%d")}" AND deadline <= "{after.strftime("%m-%d")}") ORDER BY deadline, name ASC')
    result = [dict(row) for row in cursor.fetchall()]

    tasks = []
    for i in result:
        date = f'{i["deadline"].split("-")[0]}月{i["deadline"].split("-")[1]}日'
        tasks.append(f'«{i["subject"]}» {i["name"]} {date}')
    return tasks

# お知らせ関連
def add_news(event, type, body, date):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS news(type, body, date, author, id)"""
    cursor.execute(sql)
    conn.commit()

    sql = """INSERT INTO news VALUES(?, ?, ?, ?, ?)"""

    profile = line_bot_api.get_profile(event.source.user_id)
    data = ((type, body, date, profile.display_name, event.message.id))#挿入するレコードを指定
    cursor.execute(sql, data)
    conn.commit()

def show_news():
    conn = sqlite3.connect('news.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS news(type, body, date, author, id)"""
    cursor.execute(sql)
    conn.commit()

    cursor.execute(f'SELECT * FROM news WHERE (date >= "{datetime.date.today().strftime("%m-%d")}") ORDER BY date ASC')
    result = [dict(row) for row in cursor.fetchall()]

    news = []
    for i in result:
        date = f'{i["date"].split("-")[0]}月{i["date"].split("-")[1]}日'
        news.append(f'〈{i["type"]}〉 {i["body"]} {date}')
    return news

def remove_news(id):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS news(type, body, date, author, id)"""
    cursor.execute(sql)
    conn.commit()

    cursor.execute(f"DELETE FROM news WHERE id = '{id}'")
    conn.commit()

# テスト範囲関連
def add_tests(event, range, subject, date):
    if (date == '前期中間' or date == '前期期末' or date == '後期中間' or date == '後期期末'):
        conn = sqlite3.connect('term_tests.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = """CREATE TABLE IF NOT EXISTS tests(range, subject, type, author, id)"""
        cursor.execute(sql)
        conn.commit()

        sql = """INSERT INTO tests VALUES(?, ?, ?, ?, ?)"""

        profile = line_bot_api.get_profile(event.source.user_id)
        data = ((range, subject, date, profile.display_name, event.message.id))#挿入するレコードを指定
        cursor.execute(sql, data)
        conn.commit()
    else:

        conn = sqlite3.connect('tests.db')
        cursor = conn.cursor()

        sql = """CREATE TABLE IF NOT EXISTS tests(range, subject, date, author, id)"""
        cursor.execute(sql)
        conn.commit()

        sql = """INSERT INTO tests VALUES(?, ?, ?, ?, ?)"""

        profile = line_bot_api.get_profile(event.source.user_id)
        data = ((range, subject, date, profile.display_name, event.message.id))#挿入するレコードを指定
        cursor.execute(sql, data)
        conn.commit()

def show_tests(subject):
    conn = sqlite3.connect('tests.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS tests(range, subject, date, author, id)"""
    cursor.execute(sql)
    conn.commit()

    if (subject == '今日'):
        cursor.execute(f'SELECT * FROM tests WHERE (date = "{datetime.date.today().strftime("%m-%d")}") ORDER BY date ASC')
    elif (subject == '明日'):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        cursor.execute(f'SELECT * FROM tests WHERE (date = "{tomorrow.strftime("%m-%d")}") ORDER BY date ASC')
    elif (subject == '前期中間' or subject == '前期期末' or subject == '後期中間' or subject == '後期期末'):
        conn = sqlite3.connect('term_tests.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = """CREATE TABLE IF NOT EXISTS tests(range, subject, type, author, id)"""
        cursor.execute(sql)
        conn.commit()

        cursor.execute(f'SELECT * FROM tests WHERE type = "{subject}" ORDER BY subject, range ASC')
    else:
        cursor.execute(f'SELECT * FROM tests WHERE (subject = "{subject}" AND date >= "{datetime.date.today().strftime("%m-%d")}") ORDER BY date ASC')

    result = [dict(row) for row in cursor.fetchall()]

    tests = []

    if subject == '今日' or subject == '明日' or subject == '前期中間' or subject == '前期期末' or subject == '後期中間' or subject == '後期期末':
        for i in result:
            tests.append(f'《{i["subject"]}》 {i["range"]}')
    else:
        for i in result:
            date = f'{i["date"].split("-")[0]}月{i["date"].split("-")[1]}日'
            tests.append(f'{date} {i["range"]}')
    return tests

def remove_tests(id):
    conn = sqlite3.connect('tests.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS tests(range, subject, date, author, id)"""
    cursor.execute(sql)
    conn.commit()

    cursor.execute(f"DELETE FROM tests WHERE id = '{id}'")
    conn.commit()

def remove_term_tests(id):
    conn = sqlite3.connect('term_tests.db')
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS tests(range, subject, date, author, id)"""
    cursor.execute(sql)
    conn.commit()

    cursor.execute(f"DELETE FROM tests WHERE id = '{id}'")
    conn.commit()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message(event)
    users(event)

    if banned_user(event.source.user_id) and not isAdmin(event.source.user_id):
        reply_message = TextSendMessage(text = "あなたは現在このbotを使用できません。")
    else:
        if event.message.text == '時間割':
            day_list = ["A月", "A火", "A水", "A木", "A金", "B月", "B火", "B水", "B木", "B金"]
            items = [QuickReplyButton(action = MessageAction(label = f"{day}", text = f"{day}曜日の時間割")) for day in day_list]
            reply_message = TextSendMessage(text = "何曜日の時間割かな？",quick_reply=QuickReply(items=items))

        elif event.message.text == 'テスト範囲':
            subject_list = ["英コミュ", "論理表現", "言語文化", "現代の国語", "今日", "明日", "前期中間", "前期期末", "後期中間", "後期期末"]
            items = [QuickReplyButton(action = MessageAction(label = f"{test}", text = f"テスト範囲 {test}")) for test in subject_list]
            reply_message = TextSendMessage(text = "何の範囲かな？",quick_reply=QuickReply(items=items))

        elif (event.message.text.split(' ')[0] == ('テスト範囲')) and (event.message.text.split(' ')[1] is not None):
            if event.message.text.split(' ')[1] == '今日':
                test = '\n\n'.join(show_tests('今日')) or 'なし'
                day = f"{datetime.datetime.now().month}月{datetime.datetime.now().day}日"
                reply_message = TextMessage(text = f'{day} のテスト範囲\n{test}')
            elif event.message.text.split(' ')[1] == '明日':
                test = '\n\n'.join(show_tests('明日')) or 'なし'
                day = f"{(datetime.datetime.now() + datetime.timedelta(days = 1)).month}月{(datetime.datetime.now() + datetime.timedelta(days = 1)).day}日"
                reply_message = TextMessage(text = f'{day} のテスト範囲\n{test}')
            elif event.message.text.split(' ')[1] == '前期中間' or event.message.text.split(' ')[1] == '前期期末' or event.message.text.split(' ')[1] == '後期中間' or event.message.text.split(' ')[1] == '後期期末':
                test = '\n\n'.join(show_tests(event.message.text.split(' ')[1])) or 'なし'
                day = f"{(datetime.datetime.now() + datetime.timedelta(days = 1)).month}月{(datetime.datetime.now() + datetime.timedelta(days = 1)).day}日"
                reply_message = TextMessage(text = f'{event.message.text.split(" ")[1]}のテスト範囲\n{test}')
            else:
                day = f"{datetime.datetime.now().month}月{datetime.datetime.now().day}日"
                test = '\n\n'.join(show_tests(event.message.text.split(' ')[1])) or 'なし'
                reply_message = TextMessage(text = f'{day}以降の {event.message.text.split(" ")[1]}\n{test}')

        elif event.message.text == '課題':
            day = f"{datetime.datetime.now().month}月{datetime.datetime.now().day}日"
            after_day = f"{(datetime.datetime.now() + datetime.timedelta(days = 10)).month}月{(datetime.datetime.now() + datetime.timedelta(days = 10)).day}日"
            tasks = '\n\n'.join(show_tasks())
            reply_message = TextSendMessage(text = f"{day}～{after_day} が期限の課題\n{tasks or 'なし'}")

        elif event.message.text == 'ヘルプ':
            help_list = ["使用方法", "開発者"]
            items = [QuickReplyButton(action = MessageAction(label = f"{help}", text = f"{help}")) for help in help_list]
            reply_message = TextSendMessage(text = "ヘルプの種類は何かな？",quick_reply=QuickReply(items=items))

        elif event.message.text == 'お知らせ':
            day = f"{datetime.datetime.now().month}月{datetime.datetime.now().day}日"
            news = '\n'.join(show_news())
            reply_message = TextSendMessage(text = f"{day} 以降のお知らせ\n{news or 'なし'}")

        elif event.message.text in lesson:
            reply_message = TextSendMessage(text = f"{event.message.text}\n① {lesson[event.message.text][0]}\n② {lesson[event.message.text][1]}\n③ {lesson[event.message.text][2]}\n④ {lesson[event.message.text][3]}\n⑤ {lesson[event.message.text][4]}")

        elif event.message.text in admin:
            reply_message = TextSendMessage(text = f'「{event.message.text}」の使用方法\n{admin[event.message.text]}')

        elif event.message.text.split(' ')[0] == '課題追加' or event.message.text.split(' ')[0] == '課題作成':
            task_name = event.message.text.split(' ')[1]
            task_subject = event.message.text.split(' ')[2]
            task_deadline = event.message.text.split(' ')[3]
            add_task(event, task_name, task_subject, task_deadline)
            reply_message = TextMessage(text = f'【{task_subject}】 の {task_name} を {task_deadline} までで追加しました。\n{event.message.id}')

        elif event.message.text.split(' ')[0] == 'お知らせ追加' or event.message.text.split(' ')[0] == 'お知らせ作成':
            news_type = event.message.text.split(' ')[1]
            news_body = event.message.text.split(' ')[2]
            news_date = event.message.text.split(' ')[3]
            add_news(event, news_type, news_body, news_date)
            reply_message = TextMessage(text = f'{news_date} の 【{news_type}】 {news_body} を追加しました。\n{event.message.id}')

        elif event.message.text.split(' ')[0] == 'テスト追加' or event.message.text.split(' ')[0] == 'テスト作成':
            test_range = event.message.text.split(' ')[1]
            test_subject = event.message.text.split(' ')[2]
            test_date = event.message.text.split(' ')[3]
            add_tests(event, test_range, test_subject, test_date)
            reply_message = TextMessage(text = f'{test_date}に{test_subject}のテスト{test_range}を追加しました。\n{event.message.id}')

        elif event.message.text.split(' ')[0] == 'テスト削除':
            test_id = event.message.text.split(' ')[1]
            remove_news(test_id)
            reply_message = TextMessage(text = f'テスト {test_id} を削除しました。')

        elif event.message.text.split(' ')[0] == '大テスト削除':
            test_id = event.message.text.split(' ')[1]
            remove_term_tests(test_id)
            reply_message = TextMessage(text = f'テスト {test_id} を削除しました。')

        elif event.message.text.split(' ')[0] == 'お知らせ削除':
            news_id = event.message.text.split(' ')[1]
            remove_news(news_id)
            reply_message = TextMessage(text = f'お知らせ {news_id} を削除しました。')

        elif event.message.text.split(' ')[0] == '課題削除':
            task_id = event.message.text.split(' ')[1]
            remove_task(task_id)
            reply_message = TextMessage(text = f'課題 {task_id} を削除しました。')

        elif event.message.text == 'database':
            db_list = ["messages", "news", "tasks", "term_tests", "tests", "users"]
            items = [QuickReplyButton(action = MessageAction(label = f"{db}", text = f"database {db}")) for db in db_list]
            reply_message = TextSendMessage(text = "表示するデータベースを選択",quick_reply=QuickReply(items=items))

        elif event.message.text.split(' ')[0] == 'database':
            db_name = event.message.text.split(' ')[1]
            reply_message = TextMessage(text = f'{fetch_data(db_name, db_name)}')

        elif event.message.text.split(' ')[0] == 'user':
            user = event.message.text.split(' ')[1]
            result = f'表示名: {find_user(user)[1]}\nID: {find_user(user)[0]}\n作成日: {find_user(user)[4]}' or 'なし'
            reply_message = TextMessage(text = f'{result}')

        elif event.message.text.split(' ')[0] == 'ユーザー禁止':
            user_id = event.message.text.split(' ')[1]
            if isAdmin(user_id):
                reply_message = TextMessage(text = f'管理者のアカウントを指定してるよ？')
            else:
                ban_user(user_id)
                profile = line_bot_api.get_profile(user_id)
                reply_message = TextMessage(text = f'{profile.display_name} の使用を禁止しました。')

        elif event.message.text.split(' ')[0] == 'ユーザー許可':
            user_id = event.message.text.split(' ')[1]
            if isAdmin(user_id):
                reply_message = TextMessage(text = f'管理者のアカウントを指定してるよ？')
            else:
                unban_user(user_id)
                profile = line_bot_api.get_profile(user_id)
                reply_message = TextMessage(text = f'{profile.display_name} の使用禁止を解除しました。')

        elif event.message.text == 'コード':
            reply_message = TextMessage(text = 'https://github.com/yuuexa/-bot')

        else:
            reply_message = TextMessage(text = event.message.text)

    line_bot_api.reply_message(event.reply_token, messages=reply_message)

if __name__ == "__main__":
    app.run()
