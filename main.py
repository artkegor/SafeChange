import random
import sqlite3
import string
import threading
import time

import telebot

# Bot initialization (fake token)
bot = telebot.TeleBot('th1s_is_n0t_a_t0k3n')

# DB initialization
connection = sqlite3.connect('exchange_database.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS Exchanges 
(id TEXT,
text_creator TEXT,
image_creator BLOB,
text_opener TEXT,
image_opener BLOB)
''')

connection.commit()

# Multithreading initialization (to avoid sqlite3 recursive error)
lock = threading.Lock()


# Main function for first start
@bot.message_handler(commands=['start'], content_types=['text'])
def main(message):
    name_of_user = message.from_user.username
    bot.send_message(message.chat.id, 'Hello! Use /help to see available commands.')
    # TXT-logs for better reliability
    with open('usernames.txt', 'a') as file:
        file.write(f"{name_of_user} started the bot.\n")


# All commands
@bot.message_handler(commands=['help'], content_types=['text'])
def help(message):
    bot.send_message(message.chat.id,
                     'Use:\n/new_exchange - to create a new exchange\n'
                     '/open_exchange - to join existing exchange\n'
                     '/support - to contact developer\n'
                     '/donate - to give a donation\n\n'
                     'Find source code on: https://github.com/artkegor/SafeChange')


# Donations
@bot.message_handler(commands=['donate'], content_types=['text'])
def donate(message):
    bot.send_message(message.chat.id, 'If you feel great using this bot, you can support developer here:\n'
                                      'https://www.donationalerts.com/r/lypoka')


# My TG for support
@bot.message_handler(commands=['support'], content_types=['text'])
def support(message):
    bot.send_message(message.chat.id, 'Any problems? Call @lypoka.')


# Creator of exchange code side
@bot.message_handler(commands=['new_exchange'], content_types=['text'])
def new_exchange(message):
    # Generation of exchange code and inserting it to DB
    global new_code
    new_code = generate_code()
    bot.send_message(message.chat.id, f'<code>{new_code}</code>  —  here is your code.\n'
                                      f'Send this to the person, you are exchanging information with.',
                     parse_mode='html')

    # Inserting whole exchange field in DB
    on_create_data = (new_code, '-', '-', '-', '-')
    on_create_request = 'INSERT INTO Exchanges(id, text_creator, image_creator, text_opener, image_opener) ' \
                        'VALUES (?, ?, ?, ?, ?)'
    with lock:
        cursor.execute(on_create_request, on_create_data);
        connection.commit()

    # Receiving data from user and inserting it into DB under generated code
    creator_sends_text = bot.send_message(message.chat.id,
                                          'Now send me the text or image, you want to send to another person')
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
        update_text_creator = 'UPDATE Exchanges SET text_creator = ? WHERE id = ?'
        with lock:
            cursor.execute(update_text_creator, (creator_text, new_code))
            connection.commit()
    # If data is image
    elif message.content_type == 'photo':
        creator_photo_info = bot.get_file(message.photo[-1].file_id)
        downloaded_creator_photo = bot.download_file(creator_photo_info.file_path)
        blob_creator_photo = sqlite3.Binary(downloaded_creator_photo)
        update_photo_creator = 'UPDATE Exchanges SET image_creator = ? WHERE id = ?'
        with lock:
            cursor.execute(update_photo_creator, (blob_creator_photo, new_code))
            connection.commit()
    # Unsupported type
    else:
        bot.send_message(message.chat.id, 'Bot supports only text or images. Try again')
        return
    bot.send_message(message.chat.id, 'Got your message!')

    # Receiving data from opener
    bot.send_message(message.chat.id, 'Now I am waiting the data from another person...')
    while True:
        with lock:
            cursor.execute('SELECT * FROM Exchanges WHERE id = ? AND (text_opener != "-" or image_opener != "-")',
                           (new_code,))
            rows = cursor.fetchone()
        if rows is not None:
            if rows[4] != '-':
                opener_photo_io = bytes(rows[4])
                bot.send_photo(message.chat.id, opener_photo_io)
            elif rows[3] != '-':
                bot.send_message(message.chat.id, str(rows[3]))
            with lock:
                cursor.execute('DELETE FROM Exchanges WHERE id = ?', (new_code,))
                connection.commit()
            return
        time.sleep(1)


# Opener of exchange code side
@bot.message_handler(commands=['open_exchange'], content_types=['text'])
def open_exchange(message):
    # Starting exchange from opener face
    getting_user_id = bot.send_message(message.chat.id,
                                       'Send me the code you got from another person.')
    bot.register_next_step_handler(getting_user_id, get_id)


# Getting code and checking if it exists in DB
def get_id(message):
    global id_to_check
    id_to_check = message.text
    with lock:
        cursor.execute('SELECT EXISTS(SELECT 1 FROM Exchanges WHERE id=?)', (id_to_check,))
        result = cursor.fetchone()
    if result[0]:
        bot.send_message(message.chat.id, 'Got your code!')
        # Going to the next step
        opener_sends_text = bot.send_message(message.chat.id,
                                             'Now send me the text or image you want to exchange with another person')
        bot.register_next_step_handler(opener_sends_text, send_opener_data)
    else:
        bot.send_message(message.chat.id, 'This code does not exist.')
        return


# Inserting opener data into DB
def send_opener_data(message):
    # If data is text
    if message.content_type == 'text':
        opener_text = message.text
        update_text_opener = 'UPDATE Exchanges SET text_opener = ? WHERE id = ?'
        with lock:
            cursor.execute(update_text_opener, (opener_text, id_to_check))
            connection.commit()
    # If data is image
    elif message.content_type == 'photo':
        opener_photo_info = bot.get_file(message.photo[-1].file_id)
        downloaded_opener_photo = bot.download_file(opener_photo_info.file_path)
        blob_opener_photo = sqlite3.Binary(downloaded_opener_photo)
        update_photo_opener = 'UPDATE Exchanges SET image_opener = ? WHERE id = ?'
        with lock:
            cursor.execute(update_photo_opener, (blob_opener_photo, id_to_check))
            connection.commit()
    # Unsupported type
    else:
        bot.send_message(message.chat.id, 'Bot supports only text or images. Try again')
        return
    bot.send_message(message.chat.id, 'Got your message!')

    # Receiving data from creator
    bot.send_message(message.chat.id, 'Now I am waiting the data from another person...')
    while True:
        with lock:
            cursor.execute('SELECT * FROM Exchanges WHERE id = ? AND (text_creator != "-" OR image_creator != "-")',
                           (id_to_check,))
            rows = cursor.fetchone()
        if rows is not None:
            if rows[2] != '-':
                creator_photo_io = bytes(rows[2])
                bot.send_photo(message.chat.id, creator_photo_io)
            elif rows[1] != '-':
                bot.send_message(message.chat.id, str(rows[1]))
            return
        time.sleep(1)


bot.polling(none_stop=True)
