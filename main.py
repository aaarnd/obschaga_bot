import telebot 
from telebot.types import Message, CallbackQuery

import logging
import sqlite3 
import re
from datetime import datetime
import json
import time

from config import settings
from text import *
from keyboard import * 

DATABASE = 'database.db3'
admins_list = []

def get_admins_list():
    try:
        temp = []
        conn = sqlite3.connect('database.db3')
        cursor = conn.cursor()
        cursor.execute("""
        SELECT userid 
        FROM User
        WHERE role = 'headmasters'
        """)
        rows = cursor.fetchall()
        for row in rows:
            temp.append(row[0])
        return temp
    except Exception as e:
        print(f'Ошибка при получении списка администраторов: {e}')

admins_list = get_admins_list()
print(admins_list)

def get_criteries():
    try:
        criteries = []
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM Criteria')
        result = cursor.fetchall()
        if result is None:
            print('Отстутствуют критерии в таблице критериев!')
            return
        for row in result:
            criteries.append(row[0])
        conn.close()
        return criteries
    except Exception as e:
        print(f"Ошибка при получении списка критериев: {e}")
        return


def setup_database():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            userid     INTEGER UNIQUE,
            grade      TEXT,
            gradenumber INTEGER UNIQUE,
            [group]    TEXT,
            faculty    TEXT,
            fio        TEXT,
            role       TEXT,
            have_debts INTEGER,
            room               REFERENCES Room (number) 
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Criteria (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Room (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            number UNIQUE
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Score (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date,
            criteria1,
            criteria2,
            criteria3,
            criteria4,
            criteria5,
            criteria6,
            criteria7,
            criteria8,
            criteria9,
            criteria10,
            summary,
            comment,
            reviewer          REFERENCES User (userid),
            room              REFERENCES Rooms (number) 
        )
        ''')

        conn.close()
    except Exception as e:
        print(f'Ошибка при инициализации базы данных: {e}')


setup_database()

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(token=settings.bot_token.get_secret_value())


@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message: Message) -> None:
    # Проверка чата 
    if message.chat.type == 'private':
        # Проверка роли
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT role FROM User WHERE userid = ?', (message.chat.id, ))
            role = cursor.fetchone()
            # Для каждой роли своя клавиатура с набором функций
            print(role)
            if role[0] == 'residents':
                bot.send_message(chat_id=message.chat.id, text=start_text, reply_markup=residents_markup)
            elif role[0] == 'cleankeepers':
                bot.send_message(chat_id=message.chat.id, text=start_text, reply_markup=cleankeepers_markup)
            elif role[0] == 'headmasters':
                bot.send_message(chat_id=message.chat.id, text=start_text, reply_markup=headmasters_markup)
            conn.close()
        except Exception as e:
            print(f'Ошибка при работе с базой данных: {e}')
            return
    else:
        bot.send_message(chat_id=message.chat.id, text=wrong_chat_text)
        return

@bot.callback_query_handler(func=lambda call:True)
def callback_query(call: CallbackQuery):
    req = call.data.split('_')
    if req[0] == 'inspect':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        if len(req) > 1:
            if req[1] == 'True':
                inspection_initialize(call.message, room=req[2], flag=True)
            else:
                inspection_initialize(call)
        else:
            inspection_request(call)
    elif req[0] == 'mycleanhistory':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        cleankeepers_show_my_last_five_inspections(call)
    elif req[0] == 'back':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        cmd_start(call.message)
    elif req[0] == 'myroom':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        residents_show_room_info(call)
    elif req[0] == 'cleankeeperslist':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        admins_get_cleankeepers_list(call)
    elif req[0] == 'checklastinspect':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        admins_get_last_inspection_request(call)

    bot.answer_callback_query(call.id)



def admins_get_last_inspection_request(call):
    try:
        conn = sqlite3.connect(DATABASE)   
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM User WHERE userid = ?', (call.message.chat.id, ))
        res = cursor.fetchone()
        conn.close()
        if res[0] == 'residents' or res[0] == 'cleankeepers':
            return
    except Exception as e:
        print(f'Ошибка при идентификации роли пользователя: {e}')
    answer = bot.send_message(chat_id=call.message.chat.id, text=cleankeepers_chose_room_text, reply_markup=back_markup)
    bot.register_next_step_handler(answer, admins_get_last_inspection)

def get_inspection_by_room_number(room:int):
    try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * 
                FROM Score 
                WHERE room = ?
                ORDER BY id DESC
                LIMIT 1
                ''', (str(room), ))
            rows = cursor.fetchone()
            conn.close()
            if rows == None:
                return None
            inspection = {
                'date' : rows[1],
                'summary' : rows[13],
                'comment' : rows[14],
                'room' : rows[16],
                'criteries_quantity' : rows[2],
                'reviewer' : rows[15]
            }
            criteries = rows[3:13]
            length = inspection['criteries_quantity']
            n = 0
            while n < length:
                inspection[f'criteria{n+1}'] = json.loads(criteries[n])
                n+=1
            return inspection
    except Exception as e:
        print(f'Ошибка при отображении данных о последней оценке комнаты для администратора: {e}')

def admins_get_last_inspection(message):
    room = message.text
    if admins_room_check(room):
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Room WHERE number = ?', (int(room), ))
            result = cursor.fetchone()
            if result is None:
                bot.send_message(chat_id=message.chat.id, text=cleankeepers_room_does_not_exists_text)
                bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
                cmd_start(message)
                return
            inspection = get_inspection_by_room_number(room)
            if inspection == None:
                bot.send_message(chat_id=message.chat.id, text=residents_no_inspections_found_text)
                cmd_start(message)
                return
            bot.send_message(chat_id=message.chat.id, text=get_cleankeepers_inspection_final_text(inspection=inspection), reply_markup=back_markup)
        except Exception as e:
            print(f'Ошибка при отображении данных о последней оценке комнаты для администратора: {e}')
    else:
        bot.send_message(chat_id=message.chat.id, text=cleankeepers_room_does_not_exists_text)
        cmd_start(message)
        return

def admins_room_check(room):
    return bool(re.fullmatch(r'\d{3}', room))
    

def admins_get_cleankeepers_list(call: CallbackQuery):
    try:
        conn = sqlite3.connect(DATABASE)   
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM User WHERE userid = ?', (call.message.chat.id, ))
        res = cursor.fetchone()
        conn.close()
        if res[0] == 'residents' or res[0] == 'cleankeepers':
            return
    except Exception as e:
        print(f'Ошибка при идентификации роли пользователя: {e}')
    try:
        conn = sqlite3.connect(DATABASE)   
        cursor = conn.cursor()
        cursor.execute('SELECT userid, fio, room FROM User WHERE role = "cleankeepers"')
        cleankeepers = cursor.fetchall()
        conn.close()
        bot.send_message(chat_id=call.message.chat.id, text=get_admins_cleankeepers_list_text(cleankeepers), reply_markup=back_markup)
    except Exception as e:
        print(f'Ошибка при получении списка роли пользователя: {e}')
        


def residents_show_room_info(call:CallbackQuery):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT room FROM User WHERE userid = ?', (call.message.chat.id, ))
        room = cursor.fetchone()
        cursor.execute('''
               SELECT * 
               FROM Score 
               WHERE room = ?
               ORDER BY id DESC
               LIMIT 1
            ''', (str(room[0]), ))
        rows = cursor.fetchone()
        conn.close()
        if rows == None:
            bot.send_message(chat_id=call.message.chat.id, text=residents_no_inspections_found_text)
            cmd_start(call.message)
            return
        inspection = {
            'date' : rows[1],
            'summary' : rows[13],
            'comment' : rows[14],
            'room' : rows[16],
            'criteries_quantity' : rows[2],
            'reviewer' : rows[15]
        }
        criteries = rows[3:13]
        length = inspection['criteries_quantity']
        n = 0
        while n < length:
            inspection[f'criteria{n+1}'] = json.loads(criteries[n])
            n+=1
        bot.send_message(chat_id=call.message.chat.id, text=get_cleankeepers_inspection_final_text(inspection=inspection), reply_markup=back_markup)
    except Exception as e:
        print(f'Ошибка при отображении данных о последней оценке комнаты для жителя общежития: {e}')


def cleankeepers_show_my_last_five_inspections(call: CallbackQuery) -> None:
    try:
        conn = sqlite3.connect(DATABASE)   
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM User WHERE userid = ?', (call.message.chat.id, ))
        res = cursor.fetchone()
        conn.close()
        if res[0] == 'residents':
            return
    except Exception as e:
        print(f'Ошибка при идентификации роли пользователя: {e}')
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
               SELECT date, summary, comment, reviewer, room 
               FROM Score 
               WHERE reviewer = ?
               ORDER BY id DESC
               LIMIT 5
            ''', (call.message.chat.id, ))
        result = cursor.fetchall()
        conn.close()
        if result == []:
            bot.send_message(chat_id=call.message.chat.id, text=cleankeepers_no_inspection_found_text)
            cmd_start(call.message)
        else:
            bot.send_message(chat_id=call.message.chat.id, text=get_cleankeepers_list_my_inspections(result), reply_markup=back_markup)
    except Exception as e:
        print(f'Ошибка при получении последних 5 оценок от инспектора: {e}')


        

def inspection_request(call: CallbackQuery) -> None:
    # Запрос номера комнаты
    try:
        conn = sqlite3.connect(DATABASE)   
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM User WHERE userid = ?', (call.message.chat.id, ))
        res = cursor.fetchone()
        conn.close()
        if res[0] == 'residents':
            return
    except Exception as e:
        print(f'Ошибка при идентификации роли пользователя: {e}')
    answer = bot.send_message(chat_id=call.message.chat.id, text=cleankeepers_chose_room_text, reply_markup=back_markup)
    bot.register_next_step_handler(answer, inspection_initialize)
    


def inspection_initialize(message: Message, room=None, flag=None) :
    # Инициализация словаря с результатом проверки\
    if flag == True:
        room = str(room)
    else:
        room = message.text
    print(room)
    if bool(re.fullmatch(r'\d{3}', room)):
        # Проверка комнаты на существование
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Room WHERE number = ?', (int(room), ))
            result = cursor.fetchone()
            conn.close()
            print(result)
            if result is None:
                bot.send_message(chat_id=message.chat.id, text=cleankeepers_room_does_not_exists_text)
                bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
                cmd_start(message)
                return
        except Exception as e:
            print(f'Ошибка при работе с базой данных при проверке номера комнаты: {e}')
            bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
            return
        # Успешный успех
        print(1)
        inspection = get_inspection_by_room_number(room)
        if inspection is None or flag is True:
            print(2)
            inspection = {
            'date' : '',
            'summary' : 0,
            'comment' : '',
            'room' : '',
            'criteries_quantity' : 0,
            'criteries_rated' : 0,
            'reviewer' : ''
            }
            inspection['room'] = room
            inspection['date'] = datetime.now().strftime('%d.%m.%Y %H:%M')
            inspection['reviewer'] = message.chat.id
            print(3)
            admins_get_message_clean(message=message, inspection=inspection, admins_list=admins_list, status='start')
            print(4)
            bot.send_message(chat_id=message.chat.id, text=cleankeepers_inspection_success_start_text)
            print(5)
            inspection_fill_criteries(message, inspection)
        else:
            bot.send_message(chat_id=message.chat.id, text=get_confirm_inspection_text(inspection), reply_markup=get_confrim_inspection_markup(room)) 
    else:
        bot.send_message(chat_id=message.chat.id, text=cleankeepers_wrong_room_format_text)
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        cmd_start(message)


def inspection_fill_criteries(message: Message, inspection: dict):
    if inspection['criteries_quantity'] == 0:
        # Заполнение критериев при их отсутствии
        criteries = get_criteries()
        i = 0
        length = len(criteries)
        while i < length:
            inspection[f'criteria{i+1}'] = {
                'criteria_name' : f'{criteries.pop()}',
                'criteria_score' : '',
                'criteria_comment' : ''
            }
            i += 1
        inspection['criteries_quantity'] = length 
    if inspection['criteries_quantity'] - inspection['criteries_rated'] > 0:
        answer = bot.send_message(chat_id=message.chat.id, text=get_cleankeepers_criteria_rate_text(
                                  criteria_name=inspection[f'criteria{inspection["criteries_rated"] + 1}']['criteria_name']))
        bot.register_next_step_handler(answer, inspection_fill_criteria_score, inspection)
    if inspection['criteries_quantity'] == inspection['criteries_rated']:
        inspection['summary'] = inspection_summary(inspection)
        answer = bot.send_message(chat_id=message.chat.id, text=cleankeepers_inspection_comment_text)
        bot.register_next_step_handler(answer, inspection_fill_comment, inspection)
        

def inspection_fill_criteria_score(message: Message, inspection: dict):
    try: 
        if re.fullmatch(r"[1-5]", message.text):
            if 1 <= int(message.text) <= 5:
                inspection[f'criteria{inspection["criteries_rated"] + 1}']['criteria_score'] = int(message.text)
                answer = bot.send_message(chat_id=message.chat.id, text=cleankeepers_inspection_criteria_comment_text)
                bot.register_next_step_handler(answer, inspection_fill_criteria_comment, inspection)
            else:
                answer = bot.send_message(chat_id=message.chat.id, text=cleankeepers_wrong_number_text)
                bot.register_next_step_handler(answer, inspection_fill_criteria_score, inspection)
        else:
            answer = bot.send_message(chat_id=message.chat.id, text=cleankeepers_wrong_number_text)
            bot.register_next_step_handler(answer, inspection_fill_criteria_score, inspection)  
    except Exception as e:
        print(f'Ошибка при оценке критериев: {e}')


def inspection_fill_criteria_comment(message: Message, inspection: dict):
    try:
        answer = message.text
        if answer == '-':
            inspection['criteries_rated'] += 1
            bot.send_message(chat_id=message.chat.id, text=get_cleankeepers_succes_rate(
                                                      criteria_name=inspection[f'criteria{inspection["criteries_rated"]}']['criteria_name'],
                                                      criteria_score=inspection[f'criteria{inspection["criteries_rated"]}']['criteria_score'],
                                                      criteria_comment=inspection[f'criteria{inspection["criteries_rated"]}']['criteria_comment'])                                                      
                                                      )
            inspection_fill_criteries(message, inspection)
        else:
            inspection['criteries_rated'] += 1
            inspection[f'criteria{inspection["criteries_rated"]}']['criteria_comment'] = message.text
            bot.send_message(chat_id=message.chat.id, text=get_cleankeepers_succes_rate(
                                                      criteria_name=inspection[f'criteria{inspection["criteries_rated"]}']['criteria_name'],
                                                      criteria_score=inspection[f'criteria{inspection["criteries_rated"]}']['criteria_score'],
                                                      criteria_comment=inspection[f'criteria{inspection["criteries_rated"]}']['criteria_comment'])                                                      
                                                      )
            inspection_fill_criteries(message, inspection)
    except Exception as e:
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        print(f'Ошибка при результировании оценки критерия: {e}')


def inspection_summary(inspection: dict) -> int:
    length = inspection['criteries_quantity']
    n = 0
    summary = 0
    while n < length:
        summary += inspection[f'criteria{n+1}']['criteria_score']
        n += 1
    summary /= length
    return round(summary, 2)



def inspection_fill_comment(message: Message, inspection:dict):
    if message.text == '-':
        bot.send_message(chat_id=message.chat.id, text=get_cleankeepers_inspection_final_text(inspection=inspection))
        answer = bot.send_message(chat_id=message.chat.id, text= cleankeepers_inspection_choose_text, reply_markup=cleankeepers_inspection_end_markup)
        bot.register_next_step_handler(answer, inspection_end, inspection)
    else:
        inspection['comment'] = message.text
        bot.send_message(chat_id=message.chat.id, text=get_cleankeepers_inspection_final_text(inspection=inspection))
        answer = bot.send_message(chat_id=message.chat.id, text= cleankeepers_inspection_choose_text, reply_markup=cleankeepers_inspection_end_markup)
        bot.register_next_step_handler(answer, inspection_end, inspection)
    

def inspection_end(message: Message, inspection: dict):
    if message.text == 'Отправить результаты в базу данных':
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        admins_get_message_clean(message=message, inspection=inspection, admins_list=admins_list, status='finish')
        bot.send_message(chat_id=message.chat.id, text=cleankeepers_inspection_end_text)
        inspection_fill_database(inspection)
        cmd_start(message)
    elif message.text == 'Начать инспекцию заново':
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        room = inspection['room']
        date = inspection['date']
        inspection = {
        'date' : date,
        'summary' : 0,
        'comment' : '',
        'room' : room,
        'criteries_quantity' : 0,
        'criteries_rated' : 0
        }
        inspection_fill_criteries(message, inspection)
    elif message.text == 'Отменить инспекцию и вернуться в главное меню':
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        admins_get_message_clean(message=message, inspection=inspection, admins_list=admins_list, status='cancel')
        inspection = []
        cmd_start(message)
    else:
        answer = bot.send_message(chat_id=message.chat.id, text=cleankeepers_inspection_wrong_command_text, reply_markup=cleankeepers_inspection_end_markup)
        bot.register_next_step_handler(answer, inspection_end, inspection)


def inspection_fill_database(inspection: dict):
    try:
        length = inspection['criteries_quantity']
        n = 0
        while n < length:
            inspection[f'criteria{n+1}'] = json.dumps(inspection[f'criteria{n+1}'])
            n += 1
        while length < 10:
            inspection[f'criteria{length+1}'] = None
            length += 1
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO Score (date, criteries_quantity, criteria1, criteria2, criteria3, criteria4, criteria5, criteria6, criteria7, criteria8, criteria9, criteria10, summary, comment, reviewer, room)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (inspection['date'], inspection['criteries_quantity'], inspection['criteria1'], inspection['criteria2'], inspection['criteria3'], inspection['criteria4'], inspection['criteria5'], inspection['criteria6'],
         inspection['criteria7'], inspection['criteria8'], inspection['criteria9'], inspection['criteria10'], inspection['summary'], inspection['comment'], inspection['reviewer'], inspection['room'])
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print({f'Ошибка при заполнении базы данных: {e}'})
        return


def admins_get_message_clean(message: Message, inspection: dict, admins_list: list, status: str):
    admins_list = get_admins_list()
    if admins_list == []:
        return
    for admin in admins_list:
        if inspection['reviewer'] == admin:
            continue
        if status == 'start':
            bot.send_message(chat_id=admin, text=get_admins_chat_cleanstart_text(message, inspection['room']))
        elif status == 'finish':
            bot.send_message(chat_id=admin, text=get_admins_chat_inspection_text(message,inspection))   
        elif status == 'cancel':
            bot.send_message(chat_id=admin, text=get_admins_chat_inspection_cancel(message,inspection))
   


try:
    bot.infinity_polling(none_stop=True)
except Exception as e:
    bot.send_message(chat_id=5331054480, text=e)
    time.sleep(30)


# def start_infinity_polling():
#     try:
#         bot.infinity_polling(none_stop=True)
#     except:
#         start_infinity_polling()

# start_infinity_polling()