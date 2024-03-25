from dotenv import load_dotenv
import os
from telebot import TeleBot

# Получение переменных
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = TeleBot(BOT_TOKEN, parse_mode=None)
