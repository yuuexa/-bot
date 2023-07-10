import Database
import datetime
Database = Database.Database()

class Utils:
    def isAdmin(self, user_id):
        if user_id == 'Uaf3fff4affec66cf3705df6f848fdce5':
            return True
        else:
            return False

    def strptime(self, date):
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')