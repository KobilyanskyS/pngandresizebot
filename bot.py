from config import bot
from telebot import types
from PIL import Image
import os
import glob

markup = types.ReplyKeyboardMarkup(True, False)
btn_y = types.KeyboardButton('Да')
btn_n = types.KeyboardButton('Нет')
markup.add(btn_y, btn_n)

@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/start':
        bot.send_message(message.from_user.id, "Пришлите мне изображенин и я преобразую его в формат PNG, а также я могу изменить его разрешение")
    else:
        bot.send_message(message.from_user.id, 'Ваше сообщение полно смысла, но мне сложно его понять. Вы можете нажать /start, чтобы узнать, что я могу сделать.')

@bot.message_handler(content_types=['photo'])
def main(message):
    file_info = bot.get_file(message.photo[len(message.photo)-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    print(file_info)
    global src
    src='/absolute/path/' + file_info.file_path
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.send_message(message.from_user.id, "Изменить разрешение?", reply_markup=markup)
    bot.register_next_step_handler(message, format)
    
def format(message):
    im1 = Image.open(src)
    if message.text == 'Да':
        basewidth = 512
        basehight = int((im1.size[1] * basewidth)/im1.size[0])
        im1 = im1.resize((basewidth, basehight), Image.ANTIALIAS)
        if im1.size[1] > 512:
            basehight = 512
            basewidth = int((im1.size[0] * basehight)/im1.size[1])
            im1 = im1.resize((basewidth, basehight), Image.ANTIALIAS)
        convert = src.replace(".jpg",".png")
        im1.save(convert)
        bot.send_message(message.from_user.id, "Ваше фото с изменением разрешения\nТекущее разрешение: " + str(im1.size[0]) + " на " + str(im1.size[1]) + " пикселей", reply_markup=types.ReplyKeyboardRemove())
        bot.send_document(message.chat.id, open(convert, 'rb'))
    elif message.text == 'Нет':
        convert = src.replace(".jpg",".png")
        im1.save(convert)
        bot.send_message(message.from_user.id, "Ваше фото без изменения разрешения\nТекущее разрешение: " + str(im1.size[0]) + " на " + str(im1.size[1]) + " пикселей", reply_markup=types.ReplyKeyboardRemove())
        bot.send_document(message.chat.id, open(convert, 'rb'))
    folder =  glob.glob('absolute/path/*')
    for files in folder:
        os.remove(files)
        
if __name__ == '__main__':
    bot.polling(True)