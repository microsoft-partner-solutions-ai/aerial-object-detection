from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.storage.blob import BlobServiceClient, ResourceTypes, AccountSasPermissions, generate_account_sas
from msrest.authentication import ApiKeyCredentials

from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta

import azure.functions as func
import logging, requests, math, json, os

# Set the below environment variables in Azure in Application Settings
# Azure Storage
connection_string = os.environ["AzureWebJobsStorage"]
# Custom Vision
custom_vision_prediction_key = os.environ["custom_vision_prediction_key"]
custom_vision_endpoint = os.environ["custom_vision_endpoint"]
project_id = os.environ["project_id"]
publish_iteration_name = os.environ["publish_iteration_name"]
# Computer Vision
cognitive_services_subscription_key = os.environ["cognitive_services_subscription_key"]
cognitive_services_endpoint = os.environ["cognitive_services_endpoint"]


def call_computer_vision(image):
    # Convert image to byte stream
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Prepare request
    analyze_url = cognitive_services_endpoint + "vision/v2.1/analyze"
    headers = {
        'Ocp-Apim-Subscription-Key': cognitive_services_subscription_key,
        'Content-Type': 'application/octet-stream'
        }
    params = {'visualFeatures': 'Color'}

    # Call Computer Vision API
    response = requests.post(analyze_url, headers=headers, params=params, data=img_byte_arr)
    response.raise_for_status()

    # Return color 
    return response.json()['color']['dominantColorForeground']


def call_custom_vision(image_url):
    prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": custom_vision_prediction_key})
    predictor = CustomVisionPredictionClient(custom_vision_endpoint, prediction_credentials)
    results = predictor.detect_image_url(project_id, publish_iteration_name, image_url)
    return results


def get_predicted_bbox(prediction, img_width, img_height):
    left = math.floor(prediction.bounding_box.left * img_width)
    top = math.floor(prediction.bounding_box.top * img_height) 
    height = math.ceil(prediction.bounding_box.height * img_height)
    width =  math.ceil(prediction.bounding_box.width * img_width)

    top_x = left
    top_y = top
    bottom_x = top_x + width
    bottom_y = top_y + height

    return top_x, top_y, bottom_x, bottom_y


def get_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    width = img.size[0]
    height = img.size[1]
    return img, width, height


def generate_url_with_sas(blob_uri):
    # Generate SAS token to retrieve image content from blob storage
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string)
    sas_token = generate_account_sas(
        blob_service_client.account_name,
        account_key=blob_service_client.credential.account_key,
        resource_types=ResourceTypes(object=True),
        permission=AccountSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    image_url = blob_uri + '?' + sas_token
    return image_url


def main(blob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {blob.name}")

    # generate full url with SAS token 
    url = generate_url_with_sas(blob.uri)

    # get image data and dimensions from url
    img, img_width, img_height = get_image_from_url(url)

    # call custom vision model to detect objects
    results = call_custom_vision(url)
    
    counter = 0
    for prediction in results.predictions:
        if (prediction.probability >= 0.75): # filter results by confidence threshold
            counter += 1
            
            # get bbox coordinates
            top_x, top_y, bottom_x, bottom_y = get_predicted_bbox(prediction, img_width, img_height)

            # crop and resize detected region
            cropped = img.crop((top_x, top_y, bottom_x, bottom_y))
            cropped = cropped.resize((50,50))

            # get dominant color from computer vision
            color = call_computer_vision(cropped) 

            logging.info(f"{counter} \t {prediction.tag_name} \t {prediction.probability} \t {color}")

            # placeholder: write results to your datastore here
