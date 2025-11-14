from flask import Flask, render_template
app = Flask(__name__,)

@app.route('/')
def index():
    return render_template('index.html',title="Naslovnica")
@app.route('/about')
def about():
    return render_template('about.html',title="O nama")
if __name__ == '__main__':
    app.run(debug=True)