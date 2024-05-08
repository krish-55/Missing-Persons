import cv2
import os
import face_recognition 
import json
import numpy as np
import requests
from email.message import EmailMessage
import ssl
import smtplib
from email.mime.image import MIMEImage
import folium
from mimetypes import guess_type
from pathlib import Path


def encode(image_path, number):
    # data_dir = './data/'
    img_files = [image_path]
    
    with open('encodings.json', 'r') as json_file:
        json_data = json.load(json_file)
        
    for img_file in img_files:
        img = cv2.imread(img_file)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # face_locations = face_recognition.face_locations(img)
        face_encodings = list(face_recognition.face_encodings(img)[0])
        json_data['encodings'].append(face_encodings)
        # json_data['ids'].append(img_file[:-4])
        json_data['ids'].append(str(number))
        
    with open('encodings.json', 'w') as f:
        json.dump(json_data, f)
        
    return "Encoded Sucessfully"


def get_loc():
    response = requests.get('https://ipinfo.io')
    data = response.json()
    lat, long = map(float, data['loc'].split(','))
    return lat, long


def get_nearest(my_lat, my_long):
    
    url = "https://trueway-places.p.rapidapi.com/FindPlacesNearby"

    querystring = {"location": "{}, {}".format(my_lat, my_long), "type": "police_station", "radius": "2000", "language": "en"}

    headers = {
        "X-RapidAPI-Key": "06f0419711msh6f2761d66924fddp16a7f8jsndcd35641ec9c",
        "X-RapidAPI-Host": "trueway-places.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    
    print(response)

    return response.json()
    # with open('station.json', 'r') as f:
    #     data = json.load(f)

    # return data


def create_map(target_data, lat, long):

    res = get_nearest(lat, long)['results'][0]
    res_lat, res_long = res['location']['lat'], res['location']['lng']
    m = folium.Map(location=[lat, long], zoom_start=13)
    folium.Marker(
        [res_lat, res_long] 
        # popup=f'<b>{res["name"]}</b>'
    ).add_to(m)

    map_html = m._repr_html_()

    try: 
        response= { "name" : res['name'] , "address":res['address'] , "distance" :res['distance'] , "map": map_html,
                "cname":target_data['name'], "clocation": target_data['suspectedLocation'], "cdate": target_data['lastDate'], 'cnumber': target_data['number']}
    except:
        response= { "name" : res['name'] , "address":res['address'] , "distance" :res['distance'] , "map": map_html}

    return response

def send_email(mail_receiver, name, file_path, res):
    lat, long = get_loc()
    print("*************Send Email Function************")
    mail_sender = 'krishstylishstar@gmail.com'
    mail_password = 'lkue wzcv xtgh ytru'
    subject = '#Incident Reported: Match Found'
    text = f'The person {name}; pertaining to the details you provided is found at: ({lat}, {long}). \nThe Police Station nearby has been notified with your contact details. The details of the police station are given below \n Name: {res["name"]} \n Address: {res["address"]}'

    # Create EmailMessage object
    em = EmailMessage()
    em['From'] = mail_sender
    em['To'] = mail_receiver
    em['Subject'] = subject

    # Set MIME type for HTML content
    mime_type, _ = guess_type(file_path)
    mime_type = mime_type or 'application/octet-stream'

    # Attach the main text content
    em.set_content(text)

    # Add the image as an attachment
    with open(file_path, 'rb') as file:
        file_data = file.read()
        file_name = Path(file_path).name
        em.add_attachment(file_data, maintype=mime_type.split('/')[0], subtype=mime_type.split('/')[1], filename=file_name)


    context = ssl.create_default_context()
    print("Email Authentication")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(mail_sender, mail_password)
        smtp.send_message(em)
        
    print("process done")