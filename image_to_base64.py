import base64

image_file_name = "app.png"
path_image_file = "icon/" + image_file_name
base64_output_file_name = "base64_" + image_file_name + ".txt"

with open(path_image_file, "rb") as image_file:
    base64_string = base64.b64encode(image_file.read()).decode('utf-8')
with open(base64_output_file_name, "w") as f:
    f.write(base64_string)
