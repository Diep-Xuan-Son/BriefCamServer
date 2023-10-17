from app_brief_s3_test import db, app, ROOT
from modeldbs import User
from service_ai.arcface_onnx_facereg import FaceRegRunnable
import cv2
import numpy as np
import json
import os, sys
import time

PATH_DB_FT = f"{str(ROOT)}/database_features"
with app.app_context():
	st_time = time.time()
	users = db.session.query(User).all()
	print(len(users))
	features = np.load(os.path.join(PATH_DB_FT, "db_1.npy"))
	print(features.shape)
	print("--------Duration: ", time.time() - st_time)
	# print(str(users).replace("(", "").replace(")", "").replace(",", "").replace("'", "").replace("\n ", ""))
	# ft = str(users).replace("(", "").replace(")", "").replace(",", "").replace("'", "").replace("\n ", "")
	# ft = np.fromstring(ft[1:-1], dtype=int, sep=' ')
	# print(ft)
	# print(users.feature)

	#------------------------------
	# config = {"model_path": f"{str(ROOT)}/weights/mxnet_regFace.onnx",
	# 			"imgsz": [112,112],
	# 			"conf_thres": 0.75,
	# 			"device": 'cpu'}
	# facereg = FaceRegRunnable(**config)

	# im_path = "crop1.jpg"
	# im = cv2.imread(im_path)
	# feature = facereg.get_feature_without_det([im])
	# feature = np.array([feature], dtype=np.float16)
	# # features = np.broadcast_to(feature, (100000, 5, feature.shape[2]))
	# # np.save(os.path.join(PATH_DB_FT, "db_1.npy"), features)
	# # print(features.shape)

	# # for i in range(100000):
	# # 	sys.stdout.write('\r' + str(i))
	# # 	sys.stdout.flush()
	# # 	if len(os.listdir(PATH_DB_FT)) == 0:
	# # 		db_ft = "db_1.npy"
	# # 		path_db = os.path.join(PATH_DB_FT, db_ft)
	# # 		np.save(path_db, feature)
	# # 	else:
	# # 		db_ft = f"db_{len(os.listdir(PATH_DB_FT))}.npy"
	# # 		path_db = os.path.join(PATH_DB_FT, db_ft)
	# # 		features = np.load(path_db)
	# # 		#--------add------
	# # 		features = np.concatenate((features, feature), axis=0)
	# # 		#-----subtract------
	# # 		# features = np.delete(features, 1, axis=0)
	# # 		np.save(path_db, features)

	# 	# ur = User(code=f"00109{9008839+i}", name="Son", birthday="29/04/1999", avatar=im_path, feature_db="db_1.npy")
	# 	# ur.save()