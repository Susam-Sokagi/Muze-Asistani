import cv2
import pyzbar.pyzbar as pyzbar
import logging
import torch
import sqlite3
import random
import time
import json
from transformers import BertForQuestionAnswering, BertTokenizer, pipeline
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)


################ Tanımlama ################

logging.getLogger().setLevel(logging.INFO)
PHOTO, QUESTION = range(2)

TOKEN = "token"
updater = Updater(TOKEN, use_context=True)

output_dir = 'model'
model = BertForQuestionAnswering.from_pretrained(output_dir)
tokenizer = BertTokenizer.from_pretrained(output_dir)

################ DB Baglantısı ###############

connection = sqlite3.connect('database.db', check_same_thread=False)
cursor = connection.cursor()

#qr koddan gelen name ile textini alma işlemi
def get_text(nm):
    dc1 = connection.execute("SELECT description1 FROM muze WHERE id = ? ", (nm,)).fetchall()[0][0]
    dc2 = connection.execute("SELECT description2 FROM muze WHERE id = ? ", (nm,)).fetchall()[0][0]
    dc3 = connection.execute("SELECT description3 FROM muze WHERE id = ? ", (nm,)).fetchall()[0][0]

    logging.info("\t \t \t \t ##### Name: {} Icin Aciklama Metinlerine Erisildi".format(nm))
    return dc1, dc2, dc3

############### QR Kod Okuyucu #################
def qr(img):
    image = cv2.imread(img)
    decodedObjects = pyzbar.decode(image)
    for obj in decodedObjects:
        data = obj.data.decode("utf-8")
    return data

############## BOT  ####################
def start(update, context):
    user = update.message.from_user
    update.message.reply_text(
        'Merhaba\t' + user.first_name + '\tben Müze Asistanın 🤗 \n')
    time.sleep(1)
    update.message.reply_text(' Beraber bu müzedeki eserleri keşfetmeye ne dersin? 🤠 \n ')
    time.sleep(1)
    update.message.reply_text(' Hadi başlayalımm! \n '
                              '📎(ataç simgesi) ile QR kodu yüklersen sana yardımcı olmaya hazırım')
    return PHOTO


def photo(update, context):

    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('user_photo.jpg')
    logging.info("\t \t \t \t ##### %s tarafından görsel yüklendi: %s", user.first_name, 'user_photo.jpg')
    try:
        data_name = qr('user_photo.jpg')
        logging.info("\t \t \t \t ##### %s tarafından tartılan obje: %s", user.first_name, data_name)

        name = connection.execute("SELECT name FROM muze WHERE id = ? ", (data_name,)).fetchall()[0][0]

        update.message.reply_text('Harika! 🥳 şimdi\t' + name + ' hakkında merak ettiklerini sorabilirsin \n'
                                                                'veya sana bu eser hakkında farklı sorular da önerebilirim ')
        return QUESTION
    except:
        update.message.reply_text('Birşeyler ters gitti 🧐. Tekrar dener misin.')
        return PHOTO


def question(update, context):
    negative1 = ['😶 Zor bi soru oldu sanırım. Ama cevabım, ',
                '🤔 Cevap vemek biraz zorladı ama sanırım cevabım bu. ',
                '🧐 Şasırtmacalı sorumu sordun emin olamadım. Ama bildiklerim: ']

    negative2 = ['Senin için bir sonuç buldum ama pek emin değilim.',
                 'Galiba bir terslik oldu. Pek güzel cevap bulamadım bu sefer.',
                 'Zor bi sorumu sordun. Cevap vermek pek kolay olmadı.']

    null = ['İnanamıyorum hiç cevap bulamadım🧐 . Başka bir soru sormaya ne dersin ☺️',
            'Hiç çalışmadığım yerden sordun 🤯 Bu sorunu araştıracağım🤓',
            'Geliştiricilerim bu soruyu sormanı beklemiyordu sanırım 🙄 Ne yazık ki cevap bulamadım']

    positive1 = ['😎 Tam da çalıştığım yerden sordun. İşte bildiklerim: ',
                 'Bence bu soruya bu cevap tam uyacaktır.🥳 Sorunun cevabı, ',
                 'Sanırım ben bu soruyu çözmek için geliştirilmişim 🥰 . İşte cevabım, ']

    positive2 = ['😎 Güzel bi soru sordun. İşte cevabım: ',
                 ' ',
                 ' ']


    user = update.message.from_user

    if update.message.text == '/yeniqr':
        return CommandHandler('yeniqr', newqr)
    else:
        logging.info("\t \t \t \t ##### %s tarafından sorulan soru: %s", user.first_name, update.message.text)
        photo_data = qr('user_photo.jpg')
        #max score answer
        dc1,dc2,dc3 = get_text(photo_data)
        dc=[dc1,dc2,dc3]
        a_dict = {}
        for x in list(dc):
            answer, score =answer_question(update.message.text, x)
            if ("[CLS]" in answer) or ("[UNK]" in answer):
                print(" ")
            else:
                a_dict[answer] = score
        if not a_dict:
            update.message.reply_text('{}'.format(random.choice(null)))
        else:
            answer = max(a_dict, key=a_dict.get)
            score = max(a_dict.values())
            if score >9:
                update.message.reply_text('{}{}'.format(random.choice(positive1), answer))
            elif score >4:
                update.message.reply_text('{}{}'.format(random.choice(positive2),answer))
            elif score >0:
                update.message.reply_text('{}{}'.format(random.choice(negative1), answer))
            else:
                update.message.reply_text('{} 😔 \n Yinede cevap vermek gerekirse, {}'.format(random.choice(negative2), answer))

            logging.info("\t \t \t \t ##### %s için verilen cevap: %s", update.message.text, answer)

    return QUESTION

#yeni qr
def newqr(update, context):
    update.message.reply_text(
        '📎(ataç simgesi) ile yeni QR kodunu yükleyerek keşfetmeye devam edebilirsin.')
    return PHOTO


def cancel(update, context):
    user = update.message.from_user
    logging.info("\t \t \t \t ##### %s konuşmayı sonlandırdı.", user.first_name)
    update.message.reply_text('Tekrar görüşmek üzere '+ user.first_name +'\thoscakal 😊',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('basla', start), ],
        states={ PHOTO: [MessageHandler(Filters.photo, photo)],
                 QUESTION: [MessageHandler(Filters.text, question)],
                 },

        fallbacks=[CommandHandler('bitir', cancel),
                   CommandHandler('yeniqr', newqr),
                   ]
    )
    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()


# ############################### MODEL ###############################

def answer_question(question, answer_text):
    input_ids = tokenizer.encode(question, answer_text)
    sep_index = input_ids.index(tokenizer.sep_token_id)
    num_seg_a = sep_index + 1
    num_seg_b = len(input_ids) - num_seg_a
    segment_ids = [0] * num_seg_a + [1] * num_seg_b
    assert len(segment_ids) == len(input_ids)
    pred_start, pred_end = model(torch.tensor([input_ids]), token_type_ids=torch.tensor([segment_ids]))

    # baslangıc ve bıtıs ıcın en ıyı olasılıkları secıyoruz
    start = torch.argmax(pred_start)
    end = torch.argmax(pred_end)
    # geri dönus
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    score = torch.max(pred_start)
    answer = tokens[start]


    for i in range(start + 1, end + 1):
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]
        else:
            answer += ' ' + tokens[i]

    logging.info("\t \t \t ##### Answer: {}".format(answer))
    logging.info("\t \t \t ##### Score: {}".format(score))
    return answer, score

if __name__ == '__main__':
    main()
