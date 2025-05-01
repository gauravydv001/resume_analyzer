from flask import Flask

from job_profiles import job_profile_keywords

app = Flask(__name__, template_folder='../templates')

from app import app as flask_app

if __name__ == '__main__':
    flask_app.run()