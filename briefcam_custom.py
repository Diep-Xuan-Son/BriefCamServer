import os, sys
import cv2
import numpy as np
from pathlib import Path
import json
from PIL import Image
import shutil
import time

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
PATH_DATA = os.path.join(ROOT,"data_render")
PATH_RESULT = os.path.join(ROOT,"static/assets")
if str(ROOT) not in sys.path:
	sys.path.append(str(ROOT))  # add ROOT to PATH

class BriefCam():
	def __init__(self, n_person=5, name_vid="", path_result=""):
		self.name_vid = name_vid
		self.path_result = path_result
		# if not os.path.exists(self.path_result):
		# 	os.mkdir(self.path_result)

		self.path_data = PATH_DATA
		if not os.path.exists(self.path_data):
			os.mkdir(self.path_data)

		self.path_each_data = os.path.join(PATH_DATA,name_vid)
		if not os.path.exists(self.path_each_data):
			os.mkdir(self.path_each_data)
		else:
			shutil.rmtree(self.path_each_data)
			os.mkdir(self.path_each_data)

		self.path_background_data = self.path_each_data + "_bgr"
		if not os.path.exists(self.path_background_data):
			os.mkdir(self.path_background_data)
		else:
			shutil.rmtree(self.path_background_data)
			os.mkdir(self.path_background_data)

		self.dict_data = {"information": {}, "data":{}}
		self.n_person = n_person
		self.data_convert = None
		self.data_n_person_remain = []
		self.data_check_overlap = None
		self.percent_total_frame = 0.2    # %
		self.bgr_pre = ""
		self.images = []
		self.bgrs = []
		# global percentCompleteBrief
		# percentCompleteBrief = 0.75

	def create_bgr(self, count, image, total_frame):	# b1
		# images = []
		# bgrs = []
		image = cv2.resize(image, (image.shape[1]//4, image.shape[0]//4), interpolation=cv2.INTER_AREA)
		self.images.append(image)
		if (count+1) % (total_frame*5//100) == 0:
			self.bgrs.append(np.median(self.images, axis = 0))
			self.images.clear()
		if (count+1) % (int(total_frame*self.percent_total_frame)) == 0:
			bgr_pth = os.path.join(self.path_background_data, f"bgr_{count}.jpg")
			bgr_subtract = np.median(self.bgrs, axis = 0)
			bgr_subtract = cv2.resize(bgr_subtract, (image.shape[1]*4, image.shape[0]*4), interpolation=cv2.INTER_AREA)
			cv2.imwrite(bgr_pth, bgr_subtract)
			self.bgrs.clear()

	def chooes_bgs(self, current_frame_count, frame_total):
		count_bgr = int(frame_total*self.percent_total_frame)
		# if( int(current_frame_count//2000) <=  int(frame_total//2000) - 1 ):
		if( int(current_frame_count//count_bgr) <=  int(frame_total//count_bgr) - 1 ):
			# count = 2000 + 2000 * int(current_frame_count//2000)
			count = count_bgr + count_bgr * int(current_frame_count//count_bgr) - 1
		else:
			# count = 2000 * int(current_frame_count//2000)
			count = count_bgr * int(current_frame_count//count_bgr) - 1
		path_background = os.path.join(self.path_background_data, f"bgr_{int(count)}.jpg")
		# print(path_background)
		
		if os.path.exists(path_background):
			bgr = cv2.imread(path_background)
			self.bgr_pre = bgr.copy()
		else:
			print("Don't have background image")
			bgr = self.bgr_pre

		return bgr

	def render(self, id, time, cls, bbox, im0):	#b2
		x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
		path_id_each_data = os.path.join(self.path_each_data, str(id))
		if id not in self.dict_data["data"]:
			self.dict_data["data"][id] = []
			if not os.path.exists(path_id_each_data):
				os.mkdir(path_id_each_data)
		id_obj = str(id) + "_" + str(len(self.dict_data["data"][id]))	#id-index of object
		data_obj = [id_obj, time, cls, x1, y1, x2, y2]
		self.dict_data["data"][id].append(data_obj)
		cv2.imwrite(os.path.join(path_id_each_data,id_obj+".jpg"), im0[y1:y2, x1:x2])

	def iou(self, bboxes1, bboxes2, i ,j):
		"""
		Calculates the intersection-over-union of two bounding boxes.
		Args:
		bbox1 (numpy.array, list of floats): bounding box in format x1,y1,x2,y2.
		bbox2 (numpy.array, list of floats): bounding box in format x1,y1,x2,y2.
		Returns:
		int: intersection-over-onion of bbox1, bbox2
		# """
		bboxes = np.concatenate((bboxes1, bboxes2), axis=1)
		overlaps_x0 = np.nanmax(bboxes[:,[0,4]], axis=1)
		overlaps_y0 = np.nanmax(bboxes[:,[1,5]], axis=1)
		overlaps_x1 = np.nanmin(bboxes[:,[2,6]], axis=1)
		overlaps_y1 = np.nanmin(bboxes[:,[3,7]], axis=1)
		check_overlap_x = overlaps_x1 - overlaps_x0
		check_overlap_y = overlaps_y1 - overlaps_y0
		# print(check_overlap_x>0)
		# print(check_overlap_y>0)
		check_overlap = np.all([check_overlap_x>0, check_overlap_y>0], axis=0)
		# print("-------result:", check_overlap)
		self.data_check_overlap[check_overlap,[i]] += 1
		self.data_check_overlap[check_overlap,[j]] += 1
		# print(self.data_check_overlap.shape)
		# bbox1 = [float(x) for x in bbox1]
		# bbox2 = [float(x) for x in bbox2]
		# (y0_1, x0_1, y1_1, x1_1) = bbox1
		# (y0_2, x0_2, y1_2, x1_2) = bbox2
		# # get the overlap rectangle
		# overlap_x0 = max(x0_1, x0_2)
		# overlap_y0 = max(y0_1, y0_2)
		# overlap_x1 = min(x1_1, x1_2)
		# overlap_y1 = min(y1_1, y1_2)
		# # check if there is an overlap
		# if overlap_x1 - overlap_x0 <= 0 or overlap_y1 - overlap_y0 <= 0:
		# 	return 0
		# else:
		# 	return 1
		# # if yes, calculate the ratio of the overlap to each ROI size and the unified size
		# size_1 = (x1_1 - x0_1) * (y1_1 - y0_1)
		# size_2 = (x1_2 - x0_2) * (y1_2 - y0_2)
		# size_intersection = (overlap_x1 - overlap_x0) * (overlap_y1 - overlap_y0)
		# size_union = size_1 + size_2 - size_intersection
		# return size_intersection / size_union

	def convert_data(self,min_action, data_n_person):
		data_n_person_convert = np.array([x[:min_action] for x in data_n_person], dtype=object)
		self.data_n_person_remain = [x[min_action:] for x in data_n_person if len(x[min_action:])>0]
		if self.data_convert is None:
			self.data_convert = data_n_person_convert.transpose(1,0,2)
		else:
			self.data_convert = np.concatenate((self.data_convert, data_n_person_convert.transpose(1,0,2)), axis=0)
		# print(self.data_convert.shape)

	def plot(self, x1, y1, x2, y2, time, img_background, color):
		img0 = img_background
		xyxy = [x1, y1, x2, y2]
		label = f'{time}'
		self.plot_one_box(xyxy, img0, label=label, color=color , line_thickness=3)
		# img_background = Image.fromarray(img0)
		return img_background

	def plot_one_box(self, x, im, color=None, label=None, line_thickness=3):
		# Plots one bounding box on image 'im' using OpenCV
		assert im.data.contiguous, 'Image not contiguous. Apply np.ascontiguousarray(im) to plot_on_box() input image.'
		tl = line_thickness or round(0.002 * (im.shape[0] + im.shape[1]) / 2) + 1  # line/font thickness
		color = color or [random.randint(0, 255) for _ in range(3)]
		c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
		cv2.rectangle(im, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
		if label:
			tf = max(tl - 1, 1)  # font thickness
			t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
			c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
			cv2.rectangle(im, c1, c2, color, -1, cv2.LINE_AA)  # filled
			cv2.putText(im, label, (c1[0], c1[1] - 2), 0, tl / 3, [255,255,255], thickness=tf, lineType=cv2.LINE_AA)
			# cv2.putText(im, label, (c1[0], c1[1] + int((x[3]-x[1])/4)), 0, tl / 3, color, thickness=tf, lineType=cv2.LINE_AA)

	# def brief(self, data, information, q_com, scale_percent, add_percent):	#b3
	def brief(self, data, information, scale_percent, add_percent, path_log):	#b3
		count = 0
		list_num_action = []
		data_n_person = []
		list_key = list(data)
		for id in list_key:
			if len(self.data_n_person_remain) > 0:
				data[id] = self.data_n_person_remain.pop(0) + data[id]
			data_n_person.append(data[id])
			list_num_action.append(len(data[id]))
			count += 1
			if count > self.n_person-1:
				# print(len(data_n_person))
				min_action = min(list_num_action)
				self.convert_data(min_action, data_n_person)
				count = 0
				list_num_action = []
				data_n_person = []
		if count > 0:
			max_action = max(len(x) for x in data_n_person)
			if len(self.data_n_person_remain) > 0:
				max_action_remain = max(len(x) for x in self.data_n_person_remain)
				max_action = max(max_action, max_action_remain)
			for i in range(self.n_person):
				if i < count:
					if len(data_n_person[i]) < max_action:
						data_n_person[i] += [[np.nan]*7]*(max_action-len(data_n_person[i]))
				else:
					if len(self.data_n_person_remain) > 0:
						if len(self.data_n_person_remain[0]) < max_action:
							self.data_n_person_remain[0] += [[np.nan]*7]*(max_action-len(self.data_n_person_remain[0]))
						data_n_person += [self.data_n_person_remain.pop(0)]
					else:
						data_n_person += [[[np.nan]*7]*max_action]
			self.data_convert = np.concatenate((self.data_convert, np.array(data_n_person, dtype=object).transpose(1,0,2)), axis=0)
			# print("----------aaaa: ", np.array(data_n_person).shape)
			# print("----------bbbb: ", self.data_convert.shape)

		if len(self.data_n_person_remain) > 0:
			max_action = max(len(x) for x in self.data_n_person_remain)
			for i in range(len(self.data_n_person_remain)):
				# print(self.data_n_person_remain[i])
				if len(self.data_n_person_remain[i]) < max_action:
					self.data_n_person_remain[i] += [[np.nan]*7]*(max_action-len(self.data_n_person_remain[i]))
			self.data_n_person_remain += [[[np.nan]*7]*max_action]
			self.data_convert = np.concatenate((self.data_convert, np.array(self.data_n_person_remain, dtype=object).transpose(1,0,2)), axis=0)
			# print("------reamin:", np.array(self.data_n_person_remain).shape)
			# print(self.data_convert.shape)

		self.data_check_overlap = np.zeros((self.data_convert.shape[0], self.data_convert.shape[1]), dtype=int)
		# print("--------data_check_overlap: ", self.data_check_overlap.shape)
		for i in range(1, self.n_person):
			for j in range(i):
				bboxes1 = self.data_convert[:,i,3:]
				bboxes2 = self.data_convert[:,j,3:]
				# print("-------box1: ", bboxes1)
				# print("-------box2: ", bboxes2)
				self.iou(bboxes1, bboxes2, i, j)	
		self.data_convert = self.data_convert.reshape(-1, 7)
		# print(self.data_convert.shape)
		self.data_check_overlap = self.data_check_overlap.reshape(-1)
		# print(self.data_check_overlap.shape)
		#create image brief
		out = cv2.VideoWriter(os.path.join(self.path_result,f'{self.name_vid}_brief.mp4'),cv2.VideoWriter_fourcc(*'mp4v'), information["fps"], (information["width"], information["height"]))
		color = [np.random.randint(0, 255) for _ in range(3)]
		# bgr = cv2.imread(os.path.join(self.path_background_data, "bgr_0.jpg"))
		ren_time_pre = self.data_convert[0][1]

		num_data = len(self.data_convert)
		# global percentCompleteBrief
		for i, ren in enumerate(self.data_convert):
			# if not q_com.empty():
			# 	q_com.get()
			# q_com.put(add_percent + scale_percent*(0.75 + (i+1)*0.25/num_data))
			percentComplete = (add_percent + scale_percent*(0.75 + (i+1)*0.25/num_data))*100
			with open(os.path.join(path_log,'percent.txt'), 'w') as f:
				f.write(f"{percentComplete:.2f}")
			# percentCompleteBrief = 0.75 + (i+1)*0.25/len(self.data_convert)

			if i%self.n_person == 0:
				if np.isnan(ren[1]):
					ren[1] = ren_time_pre
				current_frame_count = int(ren[1]*information["fps"])
				bgr = self.chooes_bgs(current_frame_count, information["total_frame"])

			if np.isnan(ren[3]):
				continue

			minute = 0
			hour = 0
			bgr = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
			# second_raw = ren[1].copy()
			if(ren[1] >= 60):
				minute = ren[1]//60
				if minute >= 60:
					hour = minute//60
					minute = minute - 60*hour
				ren[1] = ren[1] - 60*minute
			time = '{hour}:{minute}:{second:.2f}'.format(hour = int(hour), minute = int(minute), second = ren[1])
			id = ren[0].split("_")[0]
			path_id_each_data = os.path.join(self.path_each_data, id)
			img_render = Image.open(os.path.join(path_id_each_data, ren[0] + ".jpg"))
			if self.data_check_overlap[i] > 0:
				img_render.putalpha(80)
				bgr.paste(img_render, (int(ren[3]), int(ren[4])), img_render)
			else:
				bgr.paste(img_render, (int(ren[3]), int(ren[4])))
			bgr = cv2.cvtColor(np.asarray(bgr), cv2.COLOR_RGB2BGR)
			# cv2.rectangle(bgr, (ren[3], ren[4]), (ren[5], ren[6]), color, 2, cv2.LINE_AA)  # filled
			bgr = self.plot(ren[3], ren[4], ren[5], ren[6], time, bgr, color=color)

			if (i+1)%self.n_person == 0:
				out.write(bgr)

		out.release()
		if os.path.exists(self.path_each_data):
			shutil.rmtree(self.path_each_data)
		if os.path.exists(self.path_background_data):
			shutil.rmtree(self.path_background_data)
		print("--------count: ", count)
		print("--------output: ", os.path.join(self.path_result,f'{self.name_vid}_brief.mp4'))
		print("--------data_n_person_remain:", len(self.data_n_person_remain))
		print("Done!!!!!!!!!!!")

# def check_complete_brief():
# 	global percentCompleteBrief
# 	return percentCompleteBrief

if __name__=="__main__":
	n_person = 4
	BC = BriefCam(n_person, "video4")
	f = open(BC.path_each_data+".json")
	BC.dict_data = json.load(f)
	# print(BC.dict_data)
	information = BC.dict_data['information']
	if information['num_person'] > n_person:
		BC.n_person = n_person
	data = BC.dict_data['data']
	BC.brief(data, information)
