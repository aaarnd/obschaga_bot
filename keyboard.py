from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

headmasters_markup = InlineKeyboardMarkup(row_width=1)
headmasters_markup.add(InlineKeyboardButton(
                    text="Посмотреть список проверщиков",
                    callback_data='cleankeeperslist'
                    ),
                    InlineKeyboardButton(
                    text="Проверить комнату",
                    callback_data='inspect'
                    ),
                    InlineKeyboardButton(
                    text="Посмотреть последнюю оценку для комнаты",
                    callback_data='checklastinspect'
                    ),
)

def get_confrim_inspection_markup(room):
    confirm_markup = InlineKeyboardMarkup(row_width=1)
    confirm_markup.add(InlineKeyboardButton(
                    text="Продолжить",
                    callback_data=f'inspect_True_{room}'
                    ),
                    InlineKeyboardButton(
                    text="⬅",
                    callback_data='back'
                    ))
    return confirm_markup


cleankeepers_markup = InlineKeyboardMarkup(row_width=1)
cleankeepers_markup.add(InlineKeyboardButton(
                    text="Провести проверку комнаты на чистоту",
                    callback_data='inspect'
                    ),
                    InlineKeyboardButton(
                    text="Посмотреть последние оцененные комнаты",
                    callback_data='mycleanhistory'
                    ),
                    InlineKeyboardButton(
                    text="Отобразить информацию о моей комнате",
                    callback_data='myroom'
                    )
)


cleankeepers_inspection_end_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
cleankeepers_inspection_end_markup.add(KeyboardButton(
                                       text="Отправить результаты в базу данных",
                                       ),
                                       KeyboardButton(
                                       text="Начать инспекцию заново",
                                       ),
                                       KeyboardButton(
                                       text="Отменить инспекцию и вернуться в главное меню",
                                       ),)

residents_markup = InlineKeyboardMarkup()
residents_markup.add(InlineKeyboardButton(
                    text="Отобразить информацию о моей комнате",
                    callback_data='myroom'
                    )
)


back_markup = InlineKeyboardMarkup()
back_markup.add(InlineKeyboardButton(
                    text='⬅',
                    callback_data=f'back'
                ))
