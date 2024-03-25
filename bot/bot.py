import random
import string
import time
from config import bot
import database.database


# Main function for first start
@bot.message_handler(commands=['start'], content_types=['text'])
def main(message):
    name_of_user = message.from_user.username
    bot.send_message(message.chat.id, 'Привет!\n'
                                      'Отправь /help чтобы увидеть список команд.')


# All commands
@bot.message_handler(commands=['help'], content_types=['text'])
def help(message):
    bot.send_message(message.chat.id,
                     'Команды:\n/new_exchange - создать новый обмен\n'
                     '/open_exchange - открыть существующий обмен\n'
                     '/support - связаться с разработчиком\n'
                     '/donate - помочь нам с развитием\n\n'
                     'Исходный код: https://github.com/artkegor/SafeChange')


# Donations
@bot.message_handler(commands=['donate'], content_types=['text'])
def donate(message):
    bot.send_message(message.chat.id, 'Если тебе помог наш бот, ты можешь поддержать нас копеечкой:\n'
                                      'https://www.donationalerts.com/r/lypoka')


# My TG for support
@bot.message_handler(commands=['support'], content_types=['text'])
def support(message):
    bot.send_message(message.chat.id, 'Возникли проблемы? Пиши - @lypoka.')


# Creator of exchange code side
@bot.message_handler(commands=['new_exchange'], content_types=['text'])
def new_exchange(message):
    # Generation of exchange code and inserting it to DB
    global new_code
    new_code = generate_code()
    bot.send_message(message.chat.id, f'<code>{new_code}</code>  —  это код обмена.\n'
                                      f'Отправь его собеседнику.\n'
                                      f'Через команду /open_exchange он присоединится к обмену.',
                     parse_mode='html')

    # Receiving data from user and inserting it into DB under generated code
    database.database.insert_empty_exchange(new_code)
    creator_sends_text = bot.send_message(message.chat.id,
                                          'Теперь пришли мне текст или фотографию, '
                                          'которую ты хочешь отправить собеседнику.')
    bot.register_next_step_handler(creator_sends_text, send_creator_data)


# Generating the code
def generate_code():
    length = 30
    letters_and_digits = string.ascii_letters + string.digits
    generated_code = ''.join(random.sample(letters_and_digits, length))
    return generated_code


# Inserting creator data into DB
def send_creator_data(message):
    # If data is text
    if message.content_type == 'text':
        creator_text = message.text
        database.database.insert_creator_text(creator_text, new_code)
    # If data is image
    elif message.content_type == 'photo':
        creator_photo_info = bot.get_file(message.photo[-1].file_id)
        downloaded_creator_photo = bot.download_file(creator_photo_info.file_path)
        database.database.insert_creator_image(downloaded_creator_photo, new_code)
    # Unsupported type
    else:
        bot.send_message(message.chat.id, 'Бот поддерживает только текст или фотографии. Попробуй еще раз!')
        return
    bot.send_message(message.chat.id, 'Принял твое сообщение!\n'
                                      'Жду информацию от другого пользователя...')

    # Receiving data from opener
    timer_creator = time.time()
    while True:
        if time.time() - timer_creator > 60.0:
            database.database.delete_exchange(new_code)
            bot.send_message(message.chat.id, 'Время вышло.\nВведите /new_exchange, чтобы создать новый обмен.')
            return
        rows = database.database.receive_data_from_opener(new_code)
        if rows is not None:
            if rows[4] != '-':
                opener_photo_io = bytes(rows[4])
                bot.send_photo(message.chat.id, opener_photo_io)
            elif rows[3] != '-':
                bot.send_message(message.chat.id, str(rows[3]))
            database.database.delete_exchange(new_code)
            return
        time.sleep(1)


# Opener of exchange code side
@bot.message_handler(commands=['open_exchange'], content_types=['text'])
def open_exchange(message):
    # Starting exchange from opener face
    getting_user_id = bot.send_message(message.chat.id,
                                       'Отправь мне код, который тебе прислал собеседник.')
    bot.register_next_step_handler(getting_user_id, get_id)


# Getting code and checking if it exists in DB
def get_id(message):
    global id_to_check
    id_to_check = message.text
    result = database.database.check_if_exists(id_to_check)
    if result[0]:
        # Going to the next step
        opener_sends_text = bot.send_message(message.chat.id,
                                             'Ты присоединился к обмену!\n'
                                             'Теперь пришли мне текст или фотографию, '
                                             'которую ты хочешь отправить собеседнику.')
        bot.register_next_step_handler(opener_sends_text, send_opener_data)
    else:
        bot.send_message(message.chat.id, 'Такого кода не существует. Попробуй еще раз!')
        return


# Inserting opener data into DB
def send_opener_data(message):
    # If data is text
    if message.content_type == 'text':
        opener_text = message.text
        database.database.insert_opener_text(opener_text, id_to_check)
    # If data is image
    elif message.content_type == 'photo':
        opener_photo_info = bot.get_file(message.photo[-1].file_id)
        downloaded_opener_photo = bot.download_file(opener_photo_info.file_path)
        database.database.insert_opener_image(downloaded_opener_photo, id_to_check)
    # Unsupported type
    else:
        bot.send_message(message.chat.id, 'Бот поддерживает только текст или фотографии. Попробуй еще раз!')
        return
    bot.send_message(message.chat.id, 'Принял твое сообщение!\n'
                                      'Жду информацию от другого пользователя...')

    # Receiving data from creator
    timer_opener = time.time()
    while True:
        if time.time() - timer_opener > 10.0:
            database.database.delete_exchange(id_to_check)
            bot.send_message(message.chat.id, 'Время вышло.\nВведите /new_exchange, чтобы создать новый обмен.')
            return
        rows = database.database.retrieve_data_from_creator(id_to_check)
        if rows is not None:
            if rows[2] != '-':
                creator_photo_io = bytes(rows[2])
                bot.send_photo(message.chat.id, creator_photo_io)
            elif rows[1] != '-':
                bot.send_message(message.chat.id, str(rows[1]))
            return
        time.sleep(1)


bot.polling(none_stop=True)
