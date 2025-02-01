import base64

image_file_name = "app.png"
data_variable_name = "APP_ICON_BASE64"
path_image_file = "icon/" + image_file_name
base64_output_file_name = "base64_" + image_file_name + ".txt"

with open(path_image_file, "rb") as image_file:
    base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    base64_string =data_variable_name + " = \"\"\"" + base64_string + "\"\"\""
    
with open(base64_output_file_name, "w") as f:
    i=0
    j=0
    while i < len(base64_string):
        if j == 149:
            f.write("\n")
            j=0
        f.write(base64_string[i])
        i+=1
        j+=1
