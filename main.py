import random
import sqlite3
import string
import time

import telebot

# Bot initialization (don't show your token ^^)
bot = telebot.TeleBot('th1s_is_n0t_a_t0k3n');

# DB initialization
connection = sqlite3.connect('exchange_database.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS Exchanges 
(id TEXT,
text_creator TEXT,
text_opener TEXT)
''')

connection.commit()


# Main function for first start or help
@bot.message_handler(commands=['start'], content_types=['text'])
def main(message):
    bot.send_message(message.chat.id,
                     'Hello! Use:\n/new_exchange - to create a new exchange\n'
                     '/open_exchange - to join existing exchange\n\n'
                     'Find source code on: https://github.com/artkegor/SafeChange')


# Creator of exchange code side
@bot.message_handler(commands=['new_exchange'], content_types=['text'])
def new_exchange(message):
    # Generation of exchange code and inserting it to DB
    global new_code
    new_code = generate_code()
    bot.send_message(message.chat.id, f'<code>{new_code}</code>  —  here is your code.\n'
                                      f'Send this to the person, you are exchanging information with.',
                     parse_mode='html')

    on_create_data = (new_code, '-', '-')
    on_create_request = 'INSERT INTO Exchanges(id, text_creator, text_opener) VALUES (?, ?, ?)'
    cursor.execute(on_create_request, on_create_data);
    connection.commit()

    # Receiving text from user and inserting it into DB under generated code
    creator_sends_text = bot.send_message(message.chat.id, 'Now send me the text, you want to send to another person')
    bot.register_next_step_handler(creator_sends_text, send_creator_text)


# Generating the code
def generate_code():
    length = 30
    letters_and_digits = string.ascii_letters + string.digits
    generated_code = ''.join(random.sample(letters_and_digits, length))
    return generated_code


# Inserting creator text into DB
def send_creator_text(message):
    creator_text = message.text
    update_text_creator = 'UPDATE Exchanges SET text_creator = ? WHERE id = ?'
    cursor.execute(update_text_creator, (creator_text, new_code))
    connection.commit()
    bot.send_message(message.chat.id, 'Got your message!')

    # Receiving text from opener
    bot.send_message(message.chat.id, 'Now I am waiting the text from another person...')
    while True:
        cursor.execute('SELECT * FROM Exchanges WHERE id = ? AND text_opener != "-"',
                       (new_code,))
        rows = cursor.fetchone()
        if rows is not None:
            bot.send_message(message.chat.id, str(rows[2]))
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
    cursor.execute('SELECT EXISTS(SELECT 1 FROM Exchanges WHERE id=?)', (id_to_check,))
    result = cursor.fetchone()
    if result[0]:
        bot.send_message(message.chat.id, 'Got your code!')
        # Going to the next step
        opener_sends_text = bot.send_message(message.chat.id,
                                             'Now send me the text you want to exchange with another person')
        bot.register_next_step_handler(opener_sends_text, send_opener_text)

    else:
        bot.send_message(message.chat.id, 'This code does not exist.')
        return


# Inserting opener text into DB
def send_opener_text(message):
    opener_text = message.text
    update_text_opener = 'UPDATE Exchanges SET text_opener = ? WHERE id = ?'
    cursor.execute(update_text_opener, (opener_text, id_to_check))
    connection.commit()
    bot.send_message(message.chat.id, 'Got your message!')

    # Receiving text from creator
    bot.send_message(message.chat.id, 'Now I am waiting the text from another person...')
    while True:
        cursor.execute('SELECT * FROM Exchanges WHERE id = ? AND text_creator != "-"',
                       (id_to_check,))
        rows = cursor.fetchone()
        if rows is not None:
            bot.send_message(message.chat.id, str(rows[1]))
            return
        time.sleep(1)


bot.polling(none_stop=True)
