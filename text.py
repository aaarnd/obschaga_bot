from telebot.types import Message
import sqlite3

start_text = 'Вас приветствует бот для быта для общаги №4. Пожалуйста, выберите интересующую вас функцию.'
wrong_chat_text = 'Неверная команда для выбранного типа чата.'

cleankeepers_chose_room_text = 'Выберите комнату для инспекции'
cleankeepers_wrong_room_format_text = 'Неверный формат комнаты.'
cleankeepers_room_does_not_exists_text = 'Такой комнаты не существует.'
cleankeepers_inspection_success_start_text = 'Инспекция начата успешно.'
cleankeepers_inspection_criteria_comment_text = 'По желанию вы можете оставить комментарий к оцененному критерию, либо напишите знак прочерка (-), если не желаете этого делать.'
cleankeepers_wrong_number_text = 'Пожалуйста, введите цифру в диапазоне от 1 до 5 включительно.'
cleankeepers_inspection_comment_text = 'Оставьте общий комментарий по комнате либо напишите прочерк (-).'
cleankeepers_inspection_choose_text = 'Пожалуйста, выберите, что сделать дальше.'
cleankeepers_inspection_wrong_command_text = 'Неверно введена команда, пожалуйста, нажмите команду из списка ниже.'
cleankeepers_inspection_end_text = 'Инспекция завершена успешно.'
cleankeepers_no_inspection_found_text = 'Не найдено ни одной инспекции от вас. Попробуйте оценить комнату с помощью кнопки "Провести проверку комнаты на чистоту".'
# cleankeepers_wrong_format = 'Неверный формат введеного текста.'

residents_no_inspections_found_text = 'По вашей комнате пока что не было проведено никаких оценок.'
admins_choose_room_text = 'Выберите комнату.'

def get_confirm_inspection_text(inspection:dict):
    string = 'По запрошенной комнате найдена следующая последняя инспекция:\n\n'
    string += get_cleankeepers_inspection_final_text(inspection)
    string += "\nВы все еще хотите начать инспекцию?"
    return string

def get_admins_cleankeepers_list_text(cleankeepers):
    if cleankeepers == []:
        string = 'В базе данных на данный момент проверщиков нет.'
    else:
        string = 'Проверщики:\n\n'
        for cleankeeper in cleankeepers:
            if cleankeeper[2] is None:
                string += f'ФИО: {cleankeeper[1]}, ID пользователя: {cleankeeper[0]}\n'
            else:
                string += f'ФИО: {cleankeeper[1]}, ID пользователя: {cleankeeper[0]}, комната проживания: {cleankeeper[2]}\n'
    return string


def get_admins_chat_inspection_cancel(message: Message, inspection: dict):
    return f'Проверщик @{message.from_user.username} отменил инспекцию комнаты №{inspection["room"]}.'


def get_admins_chat_inspection_text(message: Message, inspection: dict):
    string = f'Проверщик @{message.from_user.username} только что закончил инспекцию комнаты №{inspection["room"]}:\n\n'
    string += get_cleankeepers_inspection_final_text(inspection)
    return string


def get_cleankeepers_list_my_inspections(result):
    string = f'Ваши последнии пять оценок:\n\n'
    for row in result:
        string += f'Оценка комнаты №{row[4]}:\n\n'
        string += f'Дата и время: {row[0]}\n'
        string += f'Суммарный балл: {row[1]}\n'
        string += f'Комментарий: {row[2]}\n\n'
    return string 


def get_cleankeepers_inspection_final_text(inspection: dict):
    string = f'Оценка комнаты №{inspection["room"]}:\n\n'
    string += f'Дата и время: {inspection["date"]}\n'
    length = inspection['criteries_quantity']
    n = 0 
    while n < length:
        string+= f'Имя критерия: {inspection[f"criteria{n+1}"]["criteria_name"]}\n'
        string+= f'Оценка: {inspection[f"criteria{n+1}"]["criteria_score"]}\n'
        string+= f'Комментарий: {inspection[f"criteria{n+1}"]["criteria_comment"]}\n\n'
        n += 1
    string += f'Суммарный балл: {inspection["summary"]}\n'
    string += f'Комментарий: {inspection["comment"]}\n'
    return string
    

def get_cleankeepers_criteria_rate_text(criteria_name):
    return f'Пожалуйста, введите оценку по следующему критерию от 1 до 5: {criteria_name}'


def get_cleankeepers_succes_rate(criteria_name, criteria_score, criteria_comment):
    return f'Оценка критерия {criteria_name}:\nОценка: {criteria_score}\nКомментарий: {criteria_comment}\nПереходим к оценке следующего критерия'


def get_admins_chat_cleanstart_text(message: Message, room: str) -> str:
    return f'Проверщик @{message.chat.username} начал инспекцию комнаты {room}.'