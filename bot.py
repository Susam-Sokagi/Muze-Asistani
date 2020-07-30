import cv2
import pyzbar.pyzbar as pyzbar
import logging
import torch
import sqlite3
import telegram
from transformers import BertForQuestionAnswering, BertTokenizer, pipeline
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)


################ Tanımlama ################

logging.basicConfig(format='%(asctime)-10s   %(message)s',datefmt="%Y-%m-%d-%H-%M-%S", level=logging.INFO)
logger = logging.getLogger(__name__)
PHOTO, QUESTION = range(2)

TOKEN = "TOKEN"
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

    logging.critical(" Name: {} Icin Aciklama Metnine Erisildi".format(nm))
    #text_data=dc1.fetchall()[0][0]
    #print(text_data)
    return dc1,dc2,dc3

########### DB Gezme ############


############### QR Kod Okuyucu #################
def qr(img):
    image = cv2.imread(img)
    decodedObjects = pyzbar.decode(image)
    for obj in decodedObjects:
        print("Type:", obj.type)
        data = obj.data.decode("utf-8")
        print("Data: ", data, "\n")
    return data

############## BOT  ####################
def start(update, context):
    user = update.message.from_user
    update.message.reply_text(
        'Merhaba\t' + user.first_name + '\tben Müze Asistanın 🤗 \n')
    update.message.reply_text(' Beraber bu müzedeki eserleri keşfetmeye ne dersin? 🤠 \n ')
    update.message.reply_text(' Hadi başlayalımm! \n '
                              '📎(ataç simgesi) ile QR kodu yüklersen sana yardımcı olmaya hazırım')
    return PHOTO


def photo(update, context):

    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('user_photo.jpg')
    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
    data_name = qr('user_photo.jpg')

    name = connection.execute("SELECT name FROM muze WHERE id = ? ", (data_name,)).fetchall()[0][0]

    reply_keyboard = [['SSS'], ['QUESTION']]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Harika! 🥳 şimdi\t' + name + ' hakkında merak ettiklerini sorabilirsin \n'
                                                            'veya sana bu eser hakkında farklı sorular da önerebilirim ')

    if update.message.text == 'SSS':
        return SSS(dn=data_name)
    else:
        return QUESTION


###öneri soru
def SSS(update, dn):
    q1 = connection.execute("SELECT soru1 FROM sorular WHERE id = ? ", (dn,)).fetchall()[0][0]
    q2=  connection.execute("SELECT soru2 FROM sorular WHERE id = ? ", (dn,)).fetchall()[0][0]
    q2 = connection.execute("SELECT soru3 FROM sorular WHERE id = ? ", (dn,)).fetchall()[0][0]


    button_list = [
        InlineKeyboardButton('%s', callback_data=1),
        InlineKeyboardButton('%s', callback_data=2)]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    # update.message.reply_text("Please choose from the following : ",reply_markup=reply_markup)

    answer = answer_question(update.message.text, get_text(dn))
    update.message.reply_text(answer)


def build_menu(buttons,n_cols,header_buttons=None,footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu



def question(update, context):

    user = update.message.from_user

    if update.message.text == '/yeniqr':
        return CommandHandler('yeniqr', newqr)
    else:
        logger.info("Question of %s: %s", user.first_name, update.message.text)
        photo_data = qr('user_photo.jpg')

        #max score answer
        dc1,dc2,dc3 = get_text(photo_data)
        answer1, score1 = answer_question(update.message.text, dc1)
        answer2, score2 = answer_question(update.message.text, dc2)
        answer3, score3 = answer_question(update.message.text, dc3)


        a_dict = {}
        a_dict[answer1] = score1
        a_dict[answer2] = score2
        a_dict[answer3] = score3

        answer = max(a_dict, key=a_dict.get)


        print(answer)
        print(a_dict[answer])


        # answer = answer_question(update.message.text, get_text(photo_data,update))

        #if 0< maxScore < 6:
        #   update.message.reply_text('emin değilim ama 🙄')


        if ("[CLS]" in answer) or ("[UNK]" in answer): update.message.reply_text(
            'Anlayamadım 🥺 Lütfen sorunu biraz daha spesifik sorabilir misin?'
            '\n Hadi tekrar deneyelim!  ')
        else: update.message.reply_text(answer)

        logger.info("Answer for %s: %s", update.message.text, answer)

    return QUESTION
    #return ConversationHandler('question', question)

#yeni qr
def newqr(update, context):
    update.message.reply_text(
        '📎(ataç simgesi) ile yeni QR kodunu yükleyerek keşfetmeye devam edebilirsin.')
    return PHOTO


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
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
                   CommandHandler('yeniqr', newqr)]
    )
    dp.add_handler(conv_handler)
    #dp.add_handler(CommandHandler('newqr', newqr))


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

    print("Answer: {}".format(answer))
    print("Score: {}".format(score))
    return answer, score

if __name__ == '__main__':
    main()


