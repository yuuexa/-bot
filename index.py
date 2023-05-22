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

admin_actions = {
    "使用方法": "下のメニューのいずれかを押すことでそのコマンドにあった動作をしてくれるよ！",
    "コード": "勿論陰キャパソ貫が開発してるよ！",
    "開発者": "勿論陰キャパソ貫が開発してるよ！"
}

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

exam_range = {
    "英コミュの小テスト範囲": {
        "5月30日": "-",
        "6月1日": "-",
        "6月6日": "-",
        "6月7日": "-",
        "6月13日": "-",
    },
    "論理表現の小テスト範囲": {
        "5月23日": "No52 - 59",
        "6月2日": "No60 - 67",
        "6月7日": "No68 - 77",
        "6月8日": "No78 - 91",
        "6月16日": "No92 - 104",
        "6月21日": "No104 - 111",
        # "6月22日": "No112 - 127",
        # "6月30日": "No128 - 136",
        # "7月24日": "No137 - 153",
        # "6月24日": "No154 - 168",
        # "6月24日": "No169 - 184",
    },
    "言語文化の小テスト範囲": {
        "5月22日": "No51 - 60",
        "5月31日": "No61 - 70",
        "6月1日": "No71 - 80",
        "6月5日": "全範囲",
        "6月12日": "?"
    },
    "現代の国語の小テスト範囲": {
        "5月30日": "-",
        "6月1日": "-",
        "6月6日": "-",
        "6月13日": "-",
        "6月15日": "-",
    }
}

help_select = {
    "使用方法": "下のメニューのいずれかを押すことでそのコマンドにあった動作をしてくれるよ！",
    "開発者": "勿論陰キャパソ貫が開発してるよ！"
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

def message(event):
    #DB設定
    conn = sqlite3.connect('messages.db')#データベースを作成、自動コミット機能ON
    cursor = conn.cursor() #カーソルオブジェクトを作成

    sql = """CREATE TABLE IF NOT EXISTS message(id, message)"""
    cursor.execute(sql)#executeコマンドでSQL文を実行
    conn.commit()#データベースにコミット(Excelでいう上書き保存。自動コミット設定なので不要だが一応・・)]

    sql = """INSERT INTO message VALUES(?, ?)"""#?は後で値を受け取るよという意味

    data = ((event.source.user_id, event.message.text))#挿入するレコードを指定
    cursor.execute(sql, data)#executeコマンドでSQL文を実行
    conn.commit()#コミットする

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message(event)

    if event.message.text == '時間割':
        day_list = ["A月", "A火", "A水", "A木", "A金", "B月", "B火", "B水", "B木", "B金"]
        items = [QuickReplyButton(action = MessageAction(label = f"{day}", text = f"{day}曜日の時間割")) for day in day_list]
        reply_message = TextSendMessage(text = "何曜日の時間割かな？",quick_reply=QuickReply(items=items))
    elif event.message.text == 'テスト範囲':
        subject_list = ["英コミュ", "論理表現", "言語文化", "現代の国語", "今日", "明日"]
        items = [QuickReplyButton(action = MessageAction(label = f"{subject}", text = f"{subject}の小テスト範囲")) for subject in subject_list]
        reply_message = TextSendMessage(text = "何の範囲かな？",quick_reply=QuickReply(items=items))
    elif event.message.text == '課題':
        reply_message = TextSendMessage(text = "開発中ダヨ！ちょっとまってね！")
    elif event.message.text == 'ヘルプ':
        help_list = ["使用方法", "開発者"]
        items = [QuickReplyButton(action = MessageAction(label = f"{help}", text = f"{help}")) for help in help_list]
        reply_message = TextSendMessage(text = "ヘルプの種類は何かな？",quick_reply=QuickReply(items=items))
    elif event.message.text in lesson:
        reply_message = TextSendMessage(text = f"{event.message.text}\n① {lesson[event.message.text][0]}\n② {lesson[event.message.text][1]}\n③ {lesson[event.message.text][2]}\n④ {lesson[event.message.text][3]}\n⑤ {lesson[event.message.text][4]}")
    elif event.message.text in exam_range:
        ranges = []
        for key, value in exam_range[event.message.text].items():
            ranges.append(f"{key} {value}")
        range = '\n'.join(ranges)
        reply_message = TextSendMessage(text = f'{event.message.text}\n{range}')
    elif event.message.text in help_select:
        reply_message = TextSendMessage(text = f'{event.message.text}\n{help_select[event.message.text]}')
    elif event.message.text == '明日の小テスト範囲':
        day = f"{(datetime.datetime.now() + datetime.timedelta(days = 1)).month}月{(datetime.datetime.now() + datetime.timedelta(days = 1)).day}日"
        communication = exam_range["英コミュの小テスト範囲"].get(day) or "なし"
        expression = exam_range["論理表現の小テスト範囲"].get(day) or "なし"
        culture = exam_range["言語文化の小テスト範囲"].get(day) or "なし"
        modern_japanese = exam_range["現代の国語の小テスト範囲"].get(day) or "なし"
        reply_message = TextSendMessage(text = f'{day} の小テスト範囲\n【英コミュ】 {communication}\n【論理表現】 {expression}\n【言語文化】 {culture}\n【現代の国語】 {modern_japanese}')
    elif event.message.text == '今日の小テスト範囲':
        day = f"{datetime.datetime.now().month}月{datetime.datetime.now().day}日"
        communication = exam_range["英コミュの小テスト範囲"].get(day) or "なし"
        expression = exam_range["論理表現の小テスト範囲"].get(day) or "なし"
        culture = exam_range["言語文化の小テスト範囲"].get(day) or "なし"
        modern_japanese = exam_range["現代の国語の小テスト範囲"].get(day) or "なし"
        reply_message = TextSendMessage(text = f'{day} の小テスト範囲\n【英コミュ】 {communication}\n【論理表現】 {expression}\n【言語文化】 {culture}\n【現代の国語】 {modern_japanese}')
    elif event.message.text == 'admin':
        action_list = ["課題追加", "課題削除", "課題編集"]
        items = [QuickReplyButton(action = MessageAction(label = f"{action}", text = f"{action}")) for action in action_list]
        reply_message = TextSendMessage(text = "実行の種類を選択",quick_reply=QuickReply(items=items))
    else:
        reply_message = TextSendMessage(text = event.message.text)

    line_bot_api.reply_message(event.reply_token, messages=reply_message)


if __name__ == "__main__":
    app.run()