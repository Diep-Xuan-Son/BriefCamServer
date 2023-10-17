import os
from pathlib import Path
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # yolov5 strongsort root directory
# WEIGHTS = ROOT / 'weights'

from flask            import Flask, session, Blueprint, json
from flask_restx import Resource, Api, fields, inputs
from flask_cors 	  import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from rq import Queue
from rq.command import send_stop_job_command
from rq.job import Job
from worker import conn
from track_briefcam_customv2 import track_briefcam, delete_output, PATH_LOG_ABSOLUTE
# from search_vehicle import search_vehicle
from merge_video import get_merge_video
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
# print(s.getsockname()[0])

app = Flask(__name__)

app.config.from_object('configuration.ConfigMYSQL')
print(app.config)

db = SQLAlchemy(app) # flask-sqlalchemy
migrate = Migrate(app, db)
q = Queue(connection=conn)
api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp, version='1.0', title='Brief Cam API',
	description='Brief Cam API for everyone', base_url='/api'
)
app.register_blueprint(api_bp)
CORS(app, supports_credentials=True, allow_headers=['Content-Type', 'X-ACCESS_TOKEN', 'Authorization'], origins=[f"http://{s.getsockname()[0]}:3456"])


