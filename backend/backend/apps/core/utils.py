import os
from uuid import uuid4
from django.conf import settings
from django.utils.deconstruct import deconstructible
# from googlemaps import GoogleMaps
import requests

# import needed modules for android
import android
import time
import sys, select # for loop exit


def get_location():
    # Initiate android-module
    droid = android.Android()

    # notify me
    droid.makeToast("fetching GPS data")
    print("start gps-sensor...")
    droid.startLocating()

    while True:
        # exit loop hook
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = input()
            print("exit endless loop...")
            break

        # wait for location-event
        event = droid.eventWaitFor('location',10000).result
        if event['name'] == "location":
            try:
                # try to get gps location data
                timestamp = repr(event['data']['gps']['time'])
                longitude = repr(event['data']['gps']['longitude'])
                latitude = repr(event['data']['gps']['latitude'])
                altitude = repr(event['data']['gps']['altitude'])
                speed = repr(event['data']['gps']['speed'])
                accuracy = repr(event['data']['gps']['accuracy'])
                loctype = "gps"
            except KeyError:
                # if no gps data, get the network location instead (inaccurate)
                timestamp = repr(event['data']['network']['time'])
                longitude = repr(event['data']['network']['longitude'])
                latitude = repr(event['data']['network']['latitude'])
                altitude = repr(event['data']['network']['altitude'])
                speed = repr(event['data']['network']['speed'])
                accuracy = repr(event['data']['network']['accuracy'])
                loctype = "net"

            data = loctype + ";" + timestamp + ";" + longitude + ";" + latitude + ";" + altitude + ";" + speed + ";" + accuracy

        print(data) # logging
        time.sleep(5) # wait for 5 seconds

    print("stop gps-sensor...")
    droid.stopLocating()


# Getter for Uber API
def get_products(latitude, longitude):
    # url = 'https://api.uber.com/{version}/{API}'.format(version='v1', API='products')
    url = 'https://sandbox-api.uber.com/{version}/{API}'.format(version='v1', API='products')
    params = {}
    params['server_token'] = settings.UBER_SERVER_TOKEN
    params['latitude'] = str(latitude)
    params['longitude'] = str(longitude)
    response = requests.get(url, params=params)
    return response.json()


def get_instructor_product():
    pass


def get_extension(file_name):
    name, extension = os.path.splitext(file_name)
    return extension


# http://stackoverflow.com/questions/15140942/django-imagefield-change-file-name-on-upload
@deconstructible
def generate_random_filename(path, is_64encoded=None):
    def wrapper(instance, filename):
        filename = '{}.{}'.format(uuid4().hex, get_extension(filename))
        return os.path.join(path, filename)

    def base64_wrapper(header):
        filename = '{}.{}'.format(uuid4().hex, header.split('/')[1])
        return os.path.join(path, filename)

    if is_64encoded:
        return base64_wrapper
    else:
        return wrapper


@deconstructible
class GenerateRandomFilename(object):

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)
