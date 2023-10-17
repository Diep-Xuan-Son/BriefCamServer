import requests
import json
from datetime import datetime, date
import time
import os
import subprocess
from pathlib import Path
FILE = Path(__file__).parents
ROOT = FILE[0]
	
#-------------------------------put video to storage-----------------------------------
# url = f"http://s3.openstack.demo.mqsolutions.vn/v1/AUTH_2124913abbf7435da225ded55d7d977f/videos_storage"
# payload = open('videoTest/video4.mp4', 'rb')
# # print(payload)
# starttime = datetime(2023,10,12,13,45).timestamp()
# endtime = datetime(2023,10,12,13,50).timestamp()
# print(url+f"/99/2023-10-12/{starttime}_{endtime}")
# headers = {
# 	'X-Auth-Token': "gAAAAABlKL4PoHhMbifvMHXKITNOSTZokJFOwaSw07febO4cDj1Fc9c4CBFpV5tvdn1sOWUE7DpkrR8U1gJzONTvzTWGIXpp04quNl2tnS-TgRzofuRnumiC9EGDawPEAyXypmE7exDpq5b7jf_je6gvPCh1JjajsduDsyUOKjXglFXBPaJW-Mg"
# }
# response = requests.request("PUT", url+f"/99/2023-10-12/{starttime}_{endtime}.mp4", headers=headers, data=payload)
# print(response.ok)

def get_token():
	url = "http://identity.openstack.demo.mqsolutions.vn/identity/v3/auth/tokens"
	payload = json.dumps({
		"auth": {
			"identity": {
				"methods": [
					"password"
				],
				"password": {
					"user": {
						"name": "admin",
						"domain": {
							"id": "default"
						},
						"password": "123456"
					}
				}
			},
			"scope": {
				"project": {
					"domain": {
						"id": "default"
					},
					"name": "demo"
				}
			}
		}
	})
	headers = {
		'Content-Type': 'application/json'
	}

	response = requests.request("POST", url, headers=headers, data=payload)

	header = response.headers
	subject_token = header["X-Subject-Token"]
	print("------------subject_token:", subject_token)
	catalog = response.json()["token"]["catalog"]

	auth_token = None
	for cat in catalog:
		if cat["type"]=="object-store" and len(cat["endpoints"])!=0:
			for ep in cat["endpoints"]:
				if ep["interface"]=="public":
					url = ep["url"]
					auth_token = url.split("/")[-1]
		else:
			continue
	print("--------------auth_token: ", auth_token)
	return auth_token, subject_token


def get_merge_video(start_times, end_times, camseris, folder_storage="videos_storage"):
	auth_token, subject_token = get_token()
	headers = {
	  'X-Auth-Token': subject_token
	}
	if auth_token is not None:
		url = f"http://s3.openstack.demo.mqsolutions.vn/v1/{auth_token}/{folder_storage}"

		# starttime = datetime(2023,10,12,13,30).timestamp()
		# endtime = datetime(2023,10,12,13,45).timestamp()
		# camseri = 99

		path_videos = []
		for i, starttime in enumerate(start_times):
			num_vid = int((end_times[i] - starttime)/300)
			print("----------------num_vid: ", num_vid)

			path_video_merged = f'{str(ROOT)}/static/video/video_merged/{starttime}_{end_times[i]}.mp4'
			path_info_merged = f'{os.path.splitext(path_video_merged)[0]}.txt'
			ftxt = open(path_info_merged, 'w')
			for num in range(num_vid):
				ts = starttime + num*300
				r = requests.get(url+f"/{camseris[i]}/{date.fromtimestamp(ts)}/{ts}_{ts+300}.mp4", headers=headers, allow_redirects=True)
				path_video_5m = f'{str(ROOT)}/static/video/video_download/{ts}_{ts+300}.mp4'
				
				open(path_video_5m, 'wb').write(r.content)
				ftxt.write(f"file '{path_video_5m}'\n")
			ftxt.close()

			subprocess.call(['ffmpeg', '-f', 'concat', '-safe', '0', '-y', '-i', path_info_merged, '-c', 'copy', path_video_merged])
			path_videos.append(path_video_merged)
		return {"video": path_videos}

	else:
		return {"video": None}
