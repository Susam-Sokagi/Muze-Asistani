import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import logging
import torch
from transformers import BertForQuestionAnswering, BertTokenizer, pipeline
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                    ConversationHandler)
import textwrap
import time


# DEFINE STEP               ############################

logging.basicConfig(format='%(asctime)-10s   %(message)s',datefmt="%Y-%m-%d-%H-%M-%S", level=logging.INFO)
logger = logging.getLogger(__name__)
PHOTO, QUESTION = range(2)
TOKEN = ""


model = BertForQuestionAnswering.from_pretrained("savasy/bert-base-turkish-squad")
tokenizer = BertTokenizer.from_pretrained("savasy/bert-base-turkish-squad")

# Telegram              ###################################
def start(update, context):
    update.message.reply_text(
        'Merhaba, ben Müze Asistanın. Konuşmayı sonlandırmak için /cancel diyebilirsin. \n \n'
        '📎(ataç simgesi) ile QR kodu yüklersen sana yardımcı olabilirim.')
    return PHOTO

def photo(update, context):
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('user_photo.jpg')
    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
    update.message.reply_text('Harika şimdi soru sorabilirsin')
    return QUESTION

def question(update, context):
    user = update.message.from_user
    logger.info("Question of %s: %s", user.first_name, update.message.text)

    text = '''Sanat tarihçileri için devasa bir konu olan Leonardo da Vinci’nin tablosu Mona Lisa, medeniyetinin sahip olduğu en özel parçalardan biri.
Mona Lisa tablosunda resmedilmiş kişinin gerçek ismi Lisa Gherardini. Mona Lisa, “benim kadınım Lisa” anlamına geliyor.
Orijinal tablonun boyutları 77×53 cm.
Mona Lisa tablosunun başka bir adı daha var: La Gioconda. Bu isim ise Mona Lisa’nın “Wife of Francesco del Giocondo” yani Frances del Giocondo’nun Karısı unvanına sahip olması nedeniyle verilmiş. Kesin olmamakla birlikte Mona Lisa’nın gerçekte Lisa del Giocondo olduğu düşünülüyor.
Mona Lisa tablosunun herhangi bir sigortası yok. Bunun nedeni de sigortalanamayacak kadar değerli görülmesi. Hiçbir sigorta şirketi bu riske girmek istemiyor yani.
Yüz tanımada kullanılan sisteme göre Mona Lisa’nın yüzü %83 mutlu, %9 bıkkın, %6 korkmuş ve %2 sinirli mimiklere sahip.
Mosa Lisa tablosu, ilk önce Fransa kralı I. Francis’e (I. François) satılmış. Leonardo’nun başyapıtı, kralın isteği üzerine Fontainebleau Sarayı’nda sergilenmiş.
Mona Lisa tablosu, sanat tarihçileri tarafından her zaman ön planda tutulsa da küresel ününü 1911 yılında onu çalan hırsıza borçlu.
Mona Lisa, Fransa’nın en ünlü müzesi olan Louvre’da, tabloya özel tasarlanmış bir odada sergileniyor. '''
    answer = answer_question(update.message.text, text)
    update.message.reply_text(answer)
    logger.info("Answer for %s: %s", update.message.text, answer)

    return ConversationHandler.END

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Tekrar görüşmek üzere hoscakal 😊',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={ PHOTO: [MessageHandler(Filters.photo, photo)],
                 QUESTION: [MessageHandler(Filters.text, question)],
                 },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()





# QR Kod Okuyucu         ###################################
def qr(img):
    image = cv2.imread(img)

    decodedObjects = pyzbar.decode(image)
    for obj in decodedObjects:
        print("Type:", obj.type)
        print("Data: ", obj.data.decode("utf-8"), "\n")
        return obj.data.decode("utf-8")

# ############################### MODEL ###############################

def answer_question(question, answer_text):
    input_ids = tokenizer.encode(question, answer_text)
    sep_index = input_ids.index(tokenizer.sep_token_id)
    num_seg_a = sep_index + 1
    num_seg_b = len(input_ids) - num_seg_a
    segment_ids = [0]*num_seg_a + [1]*num_seg_b
    assert len(segment_ids) == len(input_ids)
    start_scores, end_scores = model(torch.tensor([input_ids]), token_type_ids=torch.tensor([segment_ids]))
    answer_start = torch.argmax(start_scores)
    answer_end = torch.argmax(end_scores)
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    answer = tokens[answer_start]
    for i in range(answer_start + 1, answer_end + 1):
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]
        else:
            answer += ' ' + tokens[i]
    return answer

if __name__ == '__main__':
    main()
