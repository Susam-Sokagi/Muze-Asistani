import cv2, logging, sqlite3, torch
import pyzbar.pyzbar as pyzbar
from transformers import BertForQuestionAnswering, BertTokenizer, pipeline
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                    ConversationHandler)

# QR Kod Okuyucu         ###################################
def qr(img):
    image = cv2.imread(img)

    decodedObjects = pyzbar.decode(image)
    for obj in decodedObjects:
        data = obj.data.decode("utf-8")
        print("Qr Data: ", data, "\n")
    return data

###################### DB conn ##############

connection = sqlite3.connect('database.db', check_same_thread=False)

#qr koddan gelen name ile textini alma işlemi
def get_text(nm):
    dc1 = connection.execute("SELECT description1 FROM muze WHERE name = ? ", (nm,))
    logging.critical(" Name: {} Icin Aciklama Metnine Erisildi".format(nm))
    text_data=dc1.fetchall()[0][0]
    return text_data


# DEFINE STEP               ############################

#logging.basicConfig(format='%(asctime)-10s   %(message)s',datefmt="%Y-%m-%d-%H-%M-%S", level=logging.INFO)
logger = logging.getLogger(__name__)
PHOTO, QUESTION = range(2)
TOKEN = "token"

output_dir = "model"
model = BertForQuestionAnswering.from_pretrained(output_dir)
tokenizer = BertTokenizer.from_pretrained(output_dir)


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
    photo_data = qr('user_photo.jpg')
    answer = answer_question(update.message.text, get_text(photo_data))
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
    answer = tokens[start]
    score = torch.max(pred_start)

    for i in range(start + 1, end + 1):
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]
        else:
            answer += ' ' + tokens[i]

    print("Answer: {}".format(answer))
    print("Score: {}".format(score))


    return answer

if __name__ == '__main__':
    main()

