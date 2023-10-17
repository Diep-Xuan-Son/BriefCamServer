import os
# from pathlib import Path
# FILE = Path(__file__).resolve()
# ROOT = FILE.parents[0]  # yolov5 strongsort root directory
# WEIGHTS = ROOT / 'weights'

from flask            import Flask, session, Blueprint, json
from flask_restx import Resource, Api, fields, inputs
from flask_cors 	  import CORS
from rq import Queue
from rq.command import send_stop_job_command
from rq.job import Job
from worker import conn
from track_briefcam_customv2 import track_briefcam, delete_output, PATH_LOG_ABSOLUTE
# from search_vehicle import search_vehicle
from merge_video import get_merge_video
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
upload_parser.add_argument("start_times", action='append', type=float, required=True)
upload_parser.add_argument("end_times", action='append', type=float, required=True)
upload_parser.add_argument("cam_serials", action='append', type=int, required=True)
model = api.model('Item', {
	"error": fields.String(),
	"object": fields.List(fields.Integer()),
	"start_times": fields.List(fields.Float(), required=True),
	"end_times": fields.List(fields.Float(), required=True),
	"cam_serials": fields.List(fields.Integer(), required=True),
	"type_vehicle": fields.List(fields.Integer()),
}, mask='{error}')
@api.route('/briefCam')
# @api.doc(params={'videos': 'Path of videos'})
@api.expect(upload_parser)
class briefCam(Resource):
	def post(self):
		args = upload_parser.parse_args()
		# inputts = args['videos']
		objectt = args['object']

		try:
			inputts = get_merge_video(args['start_times'], args['end_times'], args['cam_serials'], folder_storage="videos_storage")
			inputts = inputts["video"]
			if inputts is None:
				return {"success": False, "error": {"message": f"Authetic token is wrong"}}

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
			job = q.enqueue_call(func=track_briefcam, args=(inputts, objectt, args['type_vehicle'], args['start_times'], args['cam_serials'], s.getsockname()[0], 10), timeout=259200, failure_ttl=30)
			print(job.id)
			return {"success": True, "idJob": job.id}

		except Exception as e:
			return {"success": False, "error": str(e)}

upload_parser1 = api.parser()
upload_parser1.add_argument("deleted", type=inputs.boolean, required=True)
upload_parser1.add_argument("jobID", type=str, required=True)
@api.expect(upload_parser1)
@api.route('/checkComplete')
class checkComplete(Resource):
	def post(self):
		args = upload_parser1.parse_args()
		
		try:
			job = Job.fetch(args['jobID'], connection=conn)
			if job.get_status() == 'failed':
				return {"success": False, "error": "No detection"}

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
			# if args['deleted']:
			# 	delete_output()

			return {"success": True, "percentComplete": percentComplete, "output": outBrief}

		except Exception as e:
			return {"success": False, "error": str(e)}

upload_parser_stopJob = api.parser()
upload_parser_stopJob.add_argument("jobID", type=str, required=True)
@api.expect(upload_parser_stopJob)
@api.route('/stopJob')
class stopJob(Resource):
	def post(self):
		try:
			args = upload_parser_stopJob.parse_args()
			send_stop_job_command(conn, args['jobID'])
			with open(os.path.join(PATH_LOG_ABSOLUTE,'percent.txt'), 'w') as f:
				f.write("0")
			# registry = q.failed_job_registry
			# print(registry.get_job_ids())
			# registry.remove(registry.get_job_ids()[-1])
			return {"success": True}

		except Exception as e:
			return {"success": False, "error": str(e)}

# upload_parser_searchVehicle = api.parser()
# upload_parser_searchVehicle.add_argument("input", type=str, required=True)
# # upload_parser_searchVehicle.add_argument("colors", action='append', type=int, required=True)
# # upload_parser_searchVehicle.add_argument("types", action='append', type=int, required=True)
# @api.expect(upload_parser_searchVehicle)
# @api.route('/searchVehicle')
# class searchVehicle(Resource):
# 	def post(self):
# 		try:
# 			args = upload_parser_searchVehicle.parse_args()
# 			# color_type = args["colors"] + args["types"]
# 			# color_type_convert = []
# 			# for i in range(19):
# 			# 	if i in color_type:
# 			# 		color_type_convert.append(1)
# 			# 	else:
# 			# 		color_type_convert.append(-1)
# 			# list_image_select = search_vehicle(args["input"], color_type_convert)
# 			colors, types = search_vehicle(args["input"])
# 			return {"success": True, "colors": colors, "types": types}

# 		except Exception as e:
# 			return {"success": False, "error": str(e)}

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=3456, debug=True)
