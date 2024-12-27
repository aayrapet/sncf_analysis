import requests
import pandas as pd
import numpy as np 

def get_names_geo_data_from_sncf_api(endpoint_suffix, **kwargs):
    base_url = "https://ressources.data.sncf.com"
    # Endpoint for the desired dataset
    endpoint = f"/api/explore/v2.1/catalog/datasets/{endpoint_suffix}/records"
    # Parameters for the API request
    params = {
        "limit": 100,  # in this API maximum limit is 100
        "offset": 0,  # we start from 0 to 100, then FROM 100 to 200 etc etc, but limit is fixed at 100, it is moving
    }
    params.update(kwargs)
    # Construct the full URL
    url = f"{base_url}{endpoint}"
    response = requests.get(url, params=params)
    wb = response.json()
    resulting_dictionnary = wb["results"].copy()
    while wb["results"] != []:
        params["offset"] = params["offset"] + 100
        response = requests.get(url, params=params)
        if response.status_code == 200:
            wb = response.json()
            for element in wb["results"]:
                resulting_dictionnary.append(element)
    # verify nb of observations
    print(
        f"nb of stations downloaded: {len(resulting_dictionnary)}, from table {endpoint_suffix}"
    )
    df = pd.json_normalize(resulting_dictionnary)
    return df

def gouv_api_addresses(data):
    
    """
    https://adresse.data.gouv.fr/api-doc/adresse

    """
   
    df=data[["lon_gare","lat_gare","nomcommune"]].copy()
    regions=[]
    
    for idx, row in df.iterrows():
        try:
            #search by lat lon 
            base_url="https://api-adresse.data.gouv.fr/reverse/"
            params = {"lat": row["lat_gare"],"lon":row["lon_gare"], "limit": 1} 
            response = requests.get(base_url, params=params)
            data = response.json()
            region=data["features"][0]["properties"]["context"].split(",")[-1].strip()
        except:  
            # if not found then search by commune name (not optimal but the only option )         
            base_url="https://api-adresse.data.gouv.fr/search/" #lat lon could not help, so search by commune name
            params = {"q":row["nomcommune"], "limit": 1}
        
            response = requests.get(base_url, params=params)
            data = response.json()
            region=data["features"][0]["properties"]["context"].split(",")[-1].strip()
           
        regions.append(region)

    return regions