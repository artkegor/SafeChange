import sqlite3
from threading import Lock

lock = Lock()

connection = sqlite3.connect('database/exchange_database.db', check_same_thread=False)
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


def delete_exchange(new_code):
    with lock:
        cursor.execute('DELETE FROM Exchanges WHERE id = ?', (new_code,))
        connection.commit()


def insert_empty_exchange(new_code):
    on_create_data = (new_code, '-', '-', '-', '-')
    on_create_request = 'INSERT INTO Exchanges(id, text_creator, image_creator, text_opener, image_opener) ' \
                        'VALUES (?, ?, ?, ?, ?)'
    with lock:
        cursor.execute(on_create_request, on_create_data);
        connection.commit()


def insert_creator_text(creator_text, new_code):
    update_text_creator = 'UPDATE Exchanges SET text_creator = ? WHERE id = ?'
    with lock:
        cursor.execute(update_text_creator, (creator_text, new_code))
        connection.commit()


def insert_creator_image(creator_img, new_code):
    blob_creator_photo = sqlite3.Binary(creator_img)
    update_photo_creator = 'UPDATE Exchanges SET image_creator = ? WHERE id = ?'
    with lock:
        cursor.execute(update_photo_creator, (blob_creator_photo, new_code))
        connection.commit()


def insert_opener_text(opener_text, id_to_check):
    update_text_opener = 'UPDATE Exchanges SET text_opener = ? WHERE id = ?'
    with lock:
        cursor.execute(update_text_opener, (opener_text, id_to_check))
        connection.commit()


def insert_opener_image(downloaded_opener_photo, id_to_check):
    blob_opener_photo = sqlite3.Binary(downloaded_opener_photo)
    update_photo_opener = 'UPDATE Exchanges SET image_opener = ? WHERE id = ?'
    with lock:
        cursor.execute(update_photo_opener, (blob_opener_photo, id_to_check))
        connection.commit()


def receive_data_from_opener(new_code):
    with lock:
        cursor.execute('SELECT * FROM Exchanges WHERE id = ? AND (text_opener != "-" or image_opener != "-")',
                       (new_code,))
        return cursor.fetchone()


def retrieve_data_from_creator(id_to_check):
    with lock:
        cursor.execute('SELECT * FROM Exchanges WHERE id = ? AND (text_creator != "-" OR image_creator != "-")',
                       (id_to_check,))
        return cursor.fetchone()


def check_if_exists(id_to_check):
    with lock:
        cursor.execute('SELECT EXISTS(SELECT 1 FROM Exchanges WHERE id=?)', (id_to_check,))
        return cursor.fetchone()
