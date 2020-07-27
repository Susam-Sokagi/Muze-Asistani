from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import logging, time, torch
from transformers import BertForQuestionAnswering, BertTokenizer

# DEFINE STEP        ############################

#logging.basicConfig(format='%(asctime)-10s   %(message)s',datefmt="%Y-%m-%d-%H-%M-%S", level=logging.INFO)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

output_dir = 'model'
model = BertForQuestionAnswering.from_pretrained(output_dir)
tokenizer = BertTokenizer.from_pretrained(output_dir)

# DATABASE  ############################
class muze(db.Model):
    name = db.Column('name', db.String(12), primary_key=True)
    description1 = db.Column(db.String(4096))
    description2 = db.Column(db.String(4096))
    description3 = db.Column(db.String(4096))

#yeni girdi ekleme işlemi
def add_data(nm, dc1, dc2= ' ', dc3=' '):
    new_data = muze(name=nm, description1=dc1, description2=dc2, description3=dc3,)
    db.session.add(new_data)
    db.session.commit()
    logging.critical("Yeni Girdi Eklendi. Name: {}".format(nm))

#girdi silme işlemi
def del_data(nm):
    muze.query.filter_by(name=nm).delete()
    db.session.commit()
    logging.critical("Girdi Silindi. Name: {}".format(nm))

#qr koddan gelen name ile textini alma işlemi
def get_text(nm):
    text = muze.query.filter_by(name=nm).first()
    dc1 = text.description1
    logging.critical(" Name: {} Icin Aciklama Metnine Erisildi".format(nm))
    return dc1

# ################################# WEB #################################
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
      message2 = "'" + message + "' mı demek istediniz?"
      time.sleep(1)
      answer = answer_question(message, get_text(id))
      return answer, 200
    else:
      message = "Öncelikle QR Kod Yüklemelisiniz."
      return message, 200
  else:
     print("error")
     return None, 404

# ############################### MODEL ###############################

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

    print("Answer: {}".format(answer))
    print("Score: {}".format(score))
    return answer

if __name__ == '__main__':
    app.run(debug='true')


