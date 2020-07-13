from flask import Flask, redirect, url_for, request, render_template
app = Flask(__name__)

id=''

@app.route('/', methods=['POST', 'GET'])
def homepage():
    if request.method == 'POST':
      message = request.form['message']
      if message:
        print(message)
        id=message
        return message, 200
      else:
        print("error")
        return None, 404
    else:
      #return render_template('index.html', data=User)
      return render_template("index.html")

@app.route('/answer', methods=['POST'])
def answer():
  message = request.form['message']
  if message and id != '':
    print(message)
    return message, 200
  else:
    print("error")
    return None, 404



if __name__ == '__main__':
    app.run(debug=True)
