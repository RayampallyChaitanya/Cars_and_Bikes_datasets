import json
import os
import os.path
from urllib.parse import urlsplit

import requests
from azure.cognitiveservices.search.imagesearch import ImageSearchAPI
from msrest.authentication import CognitiveServicesCredentials


def download_data(vehicleType):
    azure_subscription_key = "19670b769b814ebb8ecfb8a1781fffd2"
    azure_client = ImageSearchAPI( CognitiveServicesCredentials( azure_subscription_key ) )

    bikeDataAPIURL = "https://www.zigwheels.com/feedsV2/feed.php?sortdirection=popularity&country_code=in&appVersionCode=75&pageSize=1000&devicePlatform=android&cityName=delhi&api_key=z48ig11523wh02ee46849522820l246s&_v=5&pageNo=1&business_unit=bike&lang_code=en&appVersion=3.0.9&connecto_id=a3138959-5a3d-404a-9ba6-3e1ba6d4763b&_format=json&page=vehicleSearch"
    carDataAPIURL = "https://www.zigwheels.com/feedsV2/feed.php?sortdirection=popularity&country_code=in&appVersionCode=75&pageSize=1000&devicePlatform=android&cityName=delhi&api_key=z48ig11523wh02ee46849522820l246s&_v=5&pageNo=1&business_unit=car&lang_code=en&appVersion=3.0.9&connecto_id=a3138959-5a3d-404a-9ba6-3e1ba6d4763b&_format=json&page=vehicleSearch"
    if vehicleType == 'cars':
        api_url = carDataAPIURL
    elif vehicleType == 'bikes':
        api_url = bikeDataAPIURL
    else:
        raise Exception( 'value of vehicle type should be car or bike.' )
    carDataResponse = requests.get( api_url )

    carJson = carDataResponse.json()

    for vehicle in carJson['data']['items']:
        get_vehicle_details( vehicle, vehicleType, azure_client )


    threads = list()
    for vehicle in carJson['data']['items']:
        x = threading.Thread( target=get_vehicle_details, args=(vehicle, vehicleType, azure_client,) )
        threads.append( x )
        x.start()

    for index, thread in enumerate( threads ):
        logging.info( "Main    : before joining thread %d.", index )
        thread.join()
        logging.info( "Main    : thread %d done", index )


def get_vehicle_details(vehicle, vehicle_type, azure_client):
    bike_detail_api_url = "https://www.zigwheels.com/feedsV2/feed.php?modelSlug="+vehicle[
        'modelSlug']+"&country_code=in&appVersionCode=75&devicePlatform=android&cityName=delhi&api_key=z48ig11523wh02ee46849522820l246s&_v=5&business_unit=bike&lang_code=en&appVersion=3.0.9&connecto_id=a3138959-5a3d-404a-9ba6-3e1ba6d4763b&_format=json&brandSlug="+ \
                          vehicle['brandSlug']+"&page=variantSpecifications&variantSlug="
    car_detail_api_url = "https://www.zigwheels.com/feedsV2/feed.php?modelSlug="+vehicle[
        'modelSlug']+"&country_code=in&appVersionCode=75&devicePlatform=android&cityName=delhi&api_key=z48ig11523wh02ee46849522820l246s&_v=5&business_unit=car&lang_code=en&appVersion=3.0.9&connecto_id=a3138959-5a3d-404a-9ba6-3e1ba6d4763b&_format=json&brandSlug="+ \
                         vehicle['brandSlug']+"&page=variantSpecifications&variantSlug="

    if vehicle_type == 'cars':
        detail_api_url = car_detail_api_url
    elif vehicle_type == 'bikes':
        detail_api_url = bike_detail_api_url
    else:
        raise Exception( 'value of vehicle type should be car or bike.' )

    carDetailResp = requests.get( detail_api_url )

    vehicle_details = carDetailResp.json()

    print( vehicle_details )

    vehicleBrandName = vehicle_details['data']['vehicleDetail']['brandName']
    vehicleModelName = vehicle_details['data']['vehicleDetail']['modelName']

    azure_search_term = str( vehicleBrandName )+" "+vehicle_details['data']['vehicleDetail'][
        'modelName']
    azure_image_results = azure_client.images.search( query=azure_search_term )

    if azure_image_results.value:
        for img_result in azure_image_results.value[0:15]:
            image_name = os.path.splitext( os.path.basename( urlsplit( img_result.content_url ).path ) )
            dict_car = {'name': image_name[0], 'image': img_result.content_url}
            vehicle_details['data']['colors'].append( dict_car.copy() )

    else:
        print( "No image results returned!" )

    directory = vehicle_type+'/'+vehicleBrandName+"/"+vehicleModelName.replace( "\t", "" )

    if not os.path.exists( directory ):
        os.makedirs( directory )

    try:

        imageDownload = requests.get( vehicle_details['data']['vehicleDetail']['image'] )

    except requests.exceptions.RequestException as e:

        print( e.filename )

    if imageDownload.status_code == 200:
        fname = directory+"/"+vehicleBrandName+"_"+vehicleModelName.replace( "\t", "" )+".jpg"
        with open( fname, 'wb' ) as f:
            print( fname )
            f.write( imageDownload.content )

    jsonFile = directory+"/details.json"
    with open( jsonFile, 'w' ) as json_file:
        json.dump( vehicle_details, json_file )

    vehicle_colors = vehicle_details['data']['colors']
    for vehicle_color in vehicle_colors:
        directory = vehicle_type+'/'+vehicleBrandName.replace( "\t", "" )+"/"+vehicleModelName.replace( '/',
                                                                                                        '' ).replace(
            "\t", "" )

        car_color_name = vehicle_color['name'].replace( '/', '' )
        if vehicle_color['image'] == '':
            continue
        color_image_download = requests.get( vehicle_color['image'] )
        # try :
        if color_image_download.status_code == 200:
            fname = directory+"/"+car_color_name.replace( "\t", "" )+".jpg"
            with open( fname, 'wb' ) as f:
                f.write( color_image_download.content )


if __name__ == '__main__':
    download_data( 'bikes' )
    download_data( 'cars' )
