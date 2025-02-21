from flask import Flask
from flask_vercel import Vercel

app = Flask(__name__, template_folder='../templates')
vercel = Vercel(app)

from app import app as flask_app

if __name__ == '__main__':
    flask_app.run()