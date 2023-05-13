import paddleclas
import ast

# model = paddleclas.PaddleClas(model_name="vehicle_attribute", batch_size=8)
# # print(model.__dict__)
# # print(model.predictor.__dict__)
# result = model.predict(input_data="image_vehicle")
# # a = next(result)[1]
# # print(a)
# # b = ast.literal_eval(a['attributes'])
# # print(b)
# for r in result:
#     print(r)
# BATCH_SIZE = 8

def search_vehicle(data_input, color_type):
	model = paddleclas.PaddleClas(model_name="vehicle_attribute", batch_size=8)
	result = model.predict(input_data=data_input)
	list_image_select = []
	for r in result:
		for b in r:
			index_result = [i for i, x in enumerate(b['output']) if x]
			if any(index in color_type for index in index_result):
				list_image_select.append(b['filename'])
	# print(list_image_select)
	# print(len(list_image_select))
	return list_image_select

if __name__=="__main__":
	colors = [0,1,2,3,4,5,6,7,8,9]
	types = [10,11,12,13,14,15,16,17]
	data_input = "image_vehicle"
	color_type = colors + types
	search_vehicle(data_input, color_type)
# "vàng"
# "cam"
# "xanh lá cây"
# "xám"
# "đỏ"
# "xanh nước biển"
# "trắng"
# "vàng kim"
# "nâu"
# "đen"

# "sedan"
# "suv"
# "van"
# "hatchback"
# "mpv"
# "pickup"
# "bus"
# "truck"
# "estate"