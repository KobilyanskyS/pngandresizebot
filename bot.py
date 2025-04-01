import asyncio
import os
import tempfile
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from PIL import Image
import cairosvg

from config import bot_token

bot = AsyncTeleBot(bot_token)

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_y = types.KeyboardButton('Да')
btn_n = types.KeyboardButton('Нет')
markup.add(btn_y, btn_n)

SUPPORTED_FORMATS = ('jpeg', 'jpg', 'png', 'webp', 'bmp', 'gif', 'svg')

user_files = {}

def convert_image(input_path: str, output_format: str = 'png', resize: bool = False):
    """Конвертирует изображение в указанный формат и изменяет его размер, если требуется."""
    file_ext = input_path.split('.')[-1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{output_format}') as temp_file:
        output_path = temp_file.name
    
    if file_ext == 'svg':
        intermediate_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
        cairosvg.svg2png(url=input_path, write_to=intermediate_path)
        input_path = intermediate_path
    
    with Image.open(input_path) as img:
        if resize:
            base_width = 512
            new_height = int((img.height * base_width) / img.width)
            img = img.resize((base_width, new_height), Image.LANCZOS)
        img.save(output_path, format=output_format.upper())
    
    return output_path

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.send_message(
        message.chat.id, 
        "Пришлите мне изображение или файл с изображением, и я преобразую его в PNG. "
        "Также можно изменить его разрешение.",
    )

@bot.message_handler(content_types=['photo', 'document'])
async def handle_image(message):
    file_info = await bot.get_file(
        message.photo[-1].file_id if message.photo else message.document.file_id
    )
    file_ext = file_info.file_path.split('.')[-1].lower()
    
    if message.document and file_ext not in SUPPORTED_FORMATS:
        await bot.send_message(message.chat.id, "Этот формат не поддерживается.")
        return
    
    downloaded_file = await bot.download_file(file_info.file_path)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_input:
        temp_input.write(downloaded_file)
        temp_input_path = temp_input.name
    
    user_files[message.chat.id] = temp_input_path
    
    await bot.send_message(message.chat.id, "Изменить разрешение?", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ['Да', 'Нет'])
async def process_conversion(message):
    temp_input_path = user_files.get(message.chat.id)
    if not temp_input_path or not os.path.exists(temp_input_path):
        await bot.send_message(message.chat.id, "Ошибка: файл не найден.")
        return
    
    resize = message.text == 'Да'
    output_path = convert_image(temp_input_path, resize=resize)
    
    await bot.send_message(
        message.chat.id, 
        f"Готово! Текущее разрешение: {Image.open(output_path).size}",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    with open(output_path, 'rb') as output_file:
        await bot.send_document(message.chat.id, output_file)
    
    os.remove(temp_input_path)
    os.remove(output_path)
    del user_files[message.chat.id]

if __name__ == '__main__':
    asyncio.run(bot.polling())