import requests
import json
from datetime import datetime, date
import time
import os
import subprocess
from pathlib import Path
import pandas as pd
FILE = Path(__file__).parents
ROOT = FILE[0]

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
auth_token = header["X-Subject-Token"]
print(auth_token)
catalog = response.json()["token"]["catalog"]

http_token = None
for cat in catalog:
	if cat["type"]=="object-store" and len(cat["endpoints"])!=0:
		for ep in cat["endpoints"]:
			if ep["interface"]=="public":
				url = ep["url"]
				print(url)
				http_token = url.split("/")[-1]
	else:
		continue

if http_token is not None:
	print(http_token)
#-------------------------------get video storage------------------------------------
	camseri = 99
	payload = {}
	headers = {
	  'X-Auth-Token': auth_token
	}
	starttime = datetime(2023,10,12,13,35).timestamp()
	endtime = datetime(2023,10,15,13,45).timestamp()
	
	list_date = pd.date_range(start=date.fromtimestamp(starttime), end=date.fromtimestamp(endtime))
	print(list_date)
	for date in list_date.values:
		# print(str(date).split("T")[0])
		date = str(date).split("T")[0]

		url = f"http://s3.openstack.demo.mqsolutions.vn/v1/{http_token}/videos_storage?prefix={camseri}/{date}"
		response = requests.request("GET", url, headers=headers, data=payload)
		list_file = response.text.split("\n")
		# print(list_file)
		for file in list_file:
			if not file.endswith(".mp4"):
				continue
			print(file)
			startts = int(os.path.basename(file).split("_")[0])
			if startts >= starttime and startts <= endtime: 
				print(startts)


	# num_vid = int((endtime - starttime)/300)
	# print(num_vid)

	# path_video_merged = f'{str(ROOT)}/static/video/video_merged/{starttime}_{endtime}.mp4'
	# path_info_merged = f'{os.path.splitext(path_video_merged)[0]}.txt'
	# ftxt = open(path_info_merged, 'w')
	# for num in range(num_vid):
	# 	ts = starttime + num*300
	# 	r = requests.get(url+f"/{camseri}/{date.fromtimestamp(ts)}/{ts}_{ts+300}.mp4", headers=headers, allow_redirects=True)
	# 	path_video_5m = f'{str(ROOT)}/static/video/video_download/{ts}_{ts+300}.mp4'
		
	# 	open(path_video_5m, 'wb').write(r.content)
	# 	ftxt.write(f"file '{path_video_5m}'\n")
	# ftxt.close()

	# subprocess.call(['ffmpeg', '-f', 'concat', '-safe', '0', '-y', '-i', path_info_merged, '-c', 'copy', path_video_merged])
	
#-------------------------------put video to storage-----------------------------------
	# url = f"http://s3.openstack.demo.mqsolutions.vn/v1/{http_token}/videos_storage"
	# payload = open('videoTest/video4.mp4', 'rb')
	# print(payload)
	# starttime = int(datetime(2023,10,12,13,45).timestamp())
	# endtime = int(datetime(2023,10,12,13,50).timestamp())
	# print(url+f"/99/2023-10-12/{starttime}_{endtime}")
	# response = requests.request("PUT", url+f"/99/2023-10-12/{starttime}_{endtime}.mp4", headers=headers, data=payload)
	# print(response.ok)