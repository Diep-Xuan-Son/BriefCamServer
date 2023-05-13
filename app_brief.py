import os
# from pathlib import Path
# FILE = Path(__file__).resolve()
# ROOT = FILE.parents[0]  # yolov5 strongsort root directory
# WEIGHTS = ROOT / 'weights'

from flask            import Flask, session, Blueprint, json
from flask_restx import Resource, Api, fields, inputs
from flask_cors 	  import CORS
from rq import Queue
from worker import conn
from track_briefcam_custom import track_briefcam, delete_output, PATH_LOG_ABSOLUTE
from search_vehicle import search_vehicle
from datetime import timedelta
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
# print(s.getsockname()[0])

app = Flask(__name__)

# app.config.from_object('configuration.Config')
print(app.config)
app.config['file_allowed'] = ['image/png', 'image/jpeg', 'application/octet-stream']
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=365)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_POOL_SIZE'] = 100
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 100

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
	'pool_size': 100,
}

q = Queue(connection=conn)
api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp, version='1.0', title='Brief Cam API',
	description='Brief Cam API for everyone', base_url='/api'
)
app.register_blueprint(api_bp)
CORS(app, supports_credentials=True, allow_headers=['Content-Type', 'X-ACCESS_TOKEN', 'Authorization'], origins=[f"http://{s.getsockname()[0]}:3456"])

upload_parser = api.parser()
upload_parser.add_argument("object", action='append', type=int, required=True)
upload_parser.add_argument("type_vehicle", action='append', type=int)
upload_parser.add_argument("videos", action='append', type=str, required=True)
model = api.model('Item', {
	"error": fields.String(),
    "object": fields.List(fields.Integer()),
    "videos": fields.List(fields.String(), required=True),
    "type_vehicle": fields.List(fields.Integer()),
}, mask='{error}')
@api.route('/briefCam')
# @api.doc(params={'videos': 'Path of videos'})
@api.expect(upload_parser)
class briefCam(Resource):
	def post(self):
		args = upload_parser.parse_args()
		inputts = args['videos']
		objectt = args['object']

		try:
			# if objectt[0]==0:
			# 	classs = [0]
			# 	weight = WEIGHTS / "crowdhuman_yolov5m.pt"
			# elif objectt[0]==1:
			# 	classs = args['type_vehicle']
			# 	weight = WEIGHTS / "vhc_test.pt"

			not_exists = []
			for inputt in inputts:
				if os.path.exists(inputt):
					continue
				else:
					not_exists.append(inputt)
			if len(not_exists) > 0:
				not_exists = str(not_exists).strip('][')
				return {"success": False, "error": {"message": f"Path {not_exists} is not correct"}}

			with open(os.path.join(PATH_LOG_ABSOLUTE,'percent.txt'), 'w') as f:
				f.write("0")
			with open(os.path.join(PATH_LOG_ABSOLUTE,'result.txt'), 'w') as f:
				f.write("None")
			# data_input = [inputts, classs, weight, q_com, q_output]
			data_input = [inputts, objectt]
			# main(*data_input)
			job = q.enqueue_call(func=track_briefcam, args=(inputts, objectt, s.getsockname()[0]), timeout=7200)
			return {"success": True}

		except Exception as e:
			return {"success": False, "error": str(e)}

upload_parser1 = api.parser()
upload_parser1.add_argument("deleted", type=inputs.boolean, required=True)
@api.expect(upload_parser1)
@api.route('/checkComplete')
class checkComplete(Resource):
	def post(self):
		args = upload_parser1.parse_args()
		
		outBrief = []
		with open(os.path.join(PATH_LOG_ABSOLUTE,'percent.txt'), 'r') as f:
			percentComplete = f.read()
			if percentComplete == "0" or percentComplete == "0\n":
				percentComplete = None
		with open(os.path.join(PATH_LOG_ABSOLUTE,'result.txt'), 'r') as f:
			list_result = f.readlines()
			if list_result[0] == "None" or list_result[0] == "None\n":
				outBrief = None
			else:
				for result in list_result:
					outBrief.append(result.split("\n")[0])

		# 	delete_output()
		if args['deleted']:
			delete_output()

		return {"percentComplete": percentComplete, "output": outBrief}

# @api.route('/delete')
# class Delete(Resource):
# 	def post(self):
# 		delete_output()

upload_parser2 = api.parser()
upload_parser2.add_argument("input", type=str, required=True)
upload_parser2.add_argument("colors", action='append', type=int, required=True)
upload_parser2.add_argument("types", action='append', type=int, required=True)
@api.expect(upload_parser2)
@api.route('/searchVehicle')
class searchVehicle(Resource):
	def post(self):
		try:
			args = upload_parser2.parse_args()
			color_type = args["colors"] + args["types"]
			list_image_select = search_vehicle(args["input"], color_type)
			return {"error": None, "output": list_image_select}

		except Exception as e:
			return {"success": False, "error": str(e)}

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=3456, debug=True)