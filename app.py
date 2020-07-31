from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import logging
import time
import torch
import random
from transformers import BertForQuestionAnswering, BertTokenizer

################ Tanımlama ################

logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

output_dir = '/home/kenobi/Desktop/Muze-Asistani/model'
model = BertForQuestionAnswering.from_pretrained(output_dir)
tokenizer = BertTokenizer.from_pretrained(output_dir)

################ DB Baglantısı ###############

class muze(db.Model):
    id = db.Column('id', db.String(12), primary_key=True)
    description1 = db.Column(db.String(4096))
    description2 = db.Column(db.String(4096))
    description3 = db.Column(db.String(4096))

#yeni girdi ekleme işlemi
def add_data(id, dc1, dc2= ' ', dc3=' '):
    new_data = muze(id=id, description1=dc1, description2=dc2, description3=dc3,)
    db.session.add(new_data)
    db.session.commit()
    logging.info("Yeni Girdi Eklendi. Name: {}".format(id))

#girdi silme işlemi
def del_data(id):
    muze.query.filter_by(id=id).delete()
    db.session.commit()
    logging.info("Girdi Silindi. Name: {}".format(id))

#qr koddan gelen name ile textini alma işlemi
def get_text(id):
    text = muze.query.filter_by(id=id).first()
    dc1 = text.description1
    dc2 = text.description2
    dc3 = text.description3
    logging.info(" Name: {} Icin Aciklama Metnine Erisildi".format(id))
    return dc1, dc2, dc3

################ Web ###############

id = 'null'  # QR ile gelen kategori türünü tutan global değişken

# GET isteği ile anasayfayı yükleyen endpoint
@app.route('/', methods=['GET'])
def homepage():
  global id
  id = "null"
  #return render_template('index.html', data=User)
  return render_template("index.html")

# QR kod upload için POST atılan endpoint
@app.route('/qr_upload', methods=['POST'])
def qr_upload():
  qr = request.form['qr']
  if qr:
    global id
    id = qr
    qr = "QR kod başarıyla yüklendi 🤖  <br> Şimdi sorunu sorabilirsin 🤓"
    time.sleep(1)
    return qr, 200
  else:
    print("error")
    return None, 404

# Karşılıklı konuşma için POST atılan endpoint
@app.route('/answer', methods=['POST'])
def answer():
  message = request.form['message']
  if message:
    if id != 'null':
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

        logging.info("\t \t \t \t ##### Sorulan soru: %s", message)
        # max score answer
        dc1, dc2, dc3 = get_text(id)
        dc = [dc1, dc2, dc3]
        a_dict = {}
        for x in list(dc):
            answer, score = answer_question(message, x)
            if ("[CLS]" in answer) or ("[UNK]" in answer):
                print(" ")
            else:
                a_dict[answer] = score
        if not a_dict:
            answer = "{}".format(random.choice(null))
        else:
            answer = max(a_dict, key=a_dict.get)
            score = max(a_dict.values())
            if score > 9:
                answer = '{}{}'.format(random.choice(positive1), answer)
            elif score > 4:
                answer = '{}{}'.format(random.choice(positive2), answer)
            elif score > 0:
                answer = '{}{}'.format(random.choice(negative1), answer)
            else:
                answer = '{} 😔 \n Yinede cevap vermek gerekirse, {}'.format(random.choice(negative2), answer)

            logging.info("\t \t \t \t ##### Verilen cevap: %s", answer)

        return answer, 200
    else:
      message = "Öncelikle QR Kod Yüklemelisiniz."
      return message, 200
  else:
     print("error")
     return None, 404

# GET isteği ile dashboardu yükleyen endpoint
@app.route('/dashboard', methods=['GET'])
def dashboard():
  global id
  id = "null"
  #return render_template('index.html', data=User)
  return render_template("dashboard.html")
  

# GET isteği ile dashboard profil sayfasını yükleyen endpoint
@app.route('/profile', methods=['GET'])
def dashboard_profile():
  global id
  id = "null"
  #return render_template('index.html', data=User)
  return render_template("profile.html")

################ Model ###############

def answer_question(question, answer_text):
    input_ids = tokenizer.encode(question, answer_text)
    sep_index = input_ids.index(tokenizer.sep_token_id)
    num_seg_a = sep_index + 1
    num_seg_b = len(input_ids) - num_seg_a
    segment_ids = [0] * num_seg_a + [1] * num_seg_b
    assert len(segment_ids) == len(input_ids)
    pred_start, pred_end = model(torch.tensor([input_ids]), token_type_ids=torch.tensor([segment_ids]))

    #baslangıc ve bıtıs ıcın en ıyı olasılıkları secıyoruz
    start = torch.argmax(pred_start)
    end = torch.argmax(pred_end)

    #geri dönus
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    answer = tokens[start]
    score = torch.max(pred_start)

    for i in range(start + 1, end + 1):
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]
        else:
            answer += ' ' + tokens[i]

    logging.info("\t \t \t ##### Answer: {}".format(answer))
    logging.info("\t \t \t ##### Score: {}".format(score))

    return answer ,score

if __name__ == '__main__':
    app.run(debug='true')


