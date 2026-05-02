import requests

url = "https://storage.googleapis.com/qvault-webapp-dynamic-assets/course_assets/eWyYRQu.png"
response = requests.get(url)

with open("static/images/tolkien.png", "wb") as file:
    file.write(response.content)