from telegram import InlineKeyboardButton, InlineKeyboardMarkup

SC_START_OK_TEXT = "Привіт! Спершу мені потрібно взнати твої дані. Надішли свій ліцейний логін."

SC_START_DONE_TEXT = 'Привіт %s, ти вже пройшов процесс інтеграції. Більше нічого робити не треба.'

SC_LOGIN_ERROR_TEXT = "Щось дивне коїться, я не зміг знайти твій логін. Спробуй ще раз!"

SC_CONFIRMATION_OK_TEXT = "А тепер надійшли мені код підтвердження, інашке я не взнаю, що це ти."

SC_CONFIRMATION_NONE_TEXT = "Схоже ти не запросив інтеграцію з телеграмом. Спочатку зайди на сайт https://auth.vtl.in.ua"

SC_CONFIRMATION_ERROR_TEXT = "Так робити не гарно, це не твій код підтвердження. Давай все зпочатку!"

SC_FINISH_TEXT = '''Добре %s,

якщо все вірно - натисни 'Зберегти', щоб продовжити. Якщо виникла помилка - натисни 'Скинути', щоб розпочати знову.'''

SC_SET_USERNAME_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton('Зберегти', callback_data='save'),
    InlineKeyboardButton('Скинути', callback_data='reset'),
]])

SC_SAVE_USER_TEXT = "Інформацію успішно збережено!"

HELP_TEXT = '''Маленький хелп вам від мене. Я знаю три команди:
по команді /start я почну процес інтеграції;
по команді /whoami я виводжу інформацію про тебе;
І ще є /help там тебе чекає цей текст

Успіху вам і нехай переможе найсильніший, Мандрівник!'''

WHOAMI_NONE_TEXT = 'Мені про тебе нічого не відомо!'

WHOAMI_USER_TEXT = '''Ось, що мені відомо про тебе:
Логін: %s
Прізвище, ім'я: %s
'''
