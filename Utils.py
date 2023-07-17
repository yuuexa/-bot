import Database
import re
import datetime
import config
from linebot import (
    LineBotApi
)
line_bot_api = LineBotApi(config.ACCESS_TOKEN)
Database = Database.Database()

words = {
    '英コミュ' : '英語コミュニケーション',
    '論表': '論理表現',
    '現国': '現代の国語',
    '言文': '言語文化',
    '生物': 'S.E.B(生物)',
    '化学': 'S.E.C(化学)',
    '物理': 'S.E.P(物理)',
    'SEB': 'S.E.B(生物)',
    'SEC': 'S.E.C(化学)',
    'SEP': 'S.E.P(物理)',
    'S.E.B': 'S.E.B(生物)',
    'S.E.C': 'S.E.C(化学)',
    'S.E.P': 'S.E.P(物理)',
    '音楽': '音楽Ⅰ',
    '美術': '美術Ⅰ',
    'HR': 'H.R.',
    '1': 'Ⅰ',
    'I': 'Ⅰ',
}

weekday = [
    '月', '火', '水', '木', '金', '土', '日'
]
groups = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'
]
weeks = [
    'A', 'B'
]

today = datetime.date.today()

class Utils:
    def hasRole(self, user_id, role_name):
        roles = Database.filter_data('users', 'user', f'(roles = "{role_name.upper()}")')
        roles_id = []
        for i in range(len(roles )):
            roles_id.append(roles[i][0])

        if user_id in roles_id:
            return True
        else:
            return False

    def isEditable(self, author, user_id):
        if (author == user_id):
            return True
        elif (not author == user_id) and (self.hasRole(user_id, 'EDITOR') or self.hasRole(user_id, 'ADMINISTRATOR')):
            return True
        elif (not author == user_id) and (self.hasRole(user_id, 'GENERAL')):
            return False

    def isBanned(self, user_id):
        user = Database.search_data('users', 'user', f'id = "{user_id}"')
        if user[6] == '1':
            return True
        else:
            return False

    def strptime(self, date):
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')

    def format_text(self, text):
        return re.sub('({})'.format('|'.join(map(re.escape, words.keys()))), lambda m: words[m.group()], text)

    def get_tests(self, group, date):
        tests = []
        for i in Database.filter_data('tests', 'test', f'(class = "{group}" AND date = "{date}")'):
            if i[4] == ' ':
                tests.append(f'⟦{i[2]}⟧ {i[1]}')
            else:
                tests.append(f'⟦{i[2]}⟧ {i[1]} ～{i[4]}')

        return tests

    def get_tasks(self, group, date):
        tasks = []
        for i in Database.filter_data('tasks', 'task', f'(class = "{group}" AND date = "{date}")'):
            if i[4] == ' ':
                tasks.append(f'⟦{i[2]}⟧ {i[1]}')
            else:
                tasks.append(f'⟦{i[2]}⟧ {i[1]} ～{i[4]}')

        return tasks

    def get_news(self, group, date):
        news = []
        for i in Database.filter_data('news', 'news', f'(class = "{group}" AND date = "{date}")'):
            if i[4] == ' ':
                news.append(f'⟦{i[2]}⟧ {i[1]}')
            else:
                news.append(f'⟦{i[2]}⟧ {i[1]} ～{i[4]}')

        return news

    def create_timetable(self, week_flag):
        if not week_flag == '作成しない':
            for x in range(4):
                for i in weeks:
                    for j in weekday:
                        if week_flag == 'B':
                            day = today + datetime.timedelta(days=weekday.index(j) - today.weekday() + 7 + (7 * x))
                            if i == 'B':
                                day = today + datetime.timedelta(days= weekday.index(j) - today.weekday() + (7 * x))
                        else:
                            day = today + datetime.timedelta(days= weekday.index(j) - today.weekday() + (7 * x))
                            if i == 'B':
                                day = today + datetime.timedelta(days= weekday.index(j) - today.weekday() + 7 + (7 * x))
                        if j == '土' or j == '日':
                            break

                        for y in groups:
                            if Database.is_exist('timetable', 'timetable', f'(class = "{y}" AND day = "{i + j}")'):
                                timetable = Database.search_data('timetable', 'timetable', f'(class = "{y}" AND day = "{i + j}")')
                                tests = self.get_tests(y, day.strftime('%m月%d日')) or 'なし'
                                tasks = self.get_tasks(y, day.strftime('%m月%d日')) or 'なし'
                                news = self.get_news(y, day.strftime('%m月%d日')) or 'なし'
                                Database.insert_data('schedule', 'schedule', '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?', '', (day.strftime('%m月%d日'), y, timetable[2], timetable[3], timetable[4], timetable[5], timetable[6], '\n'.join(tests), '\n'.join(tasks), '\n'.join(news), '1'))