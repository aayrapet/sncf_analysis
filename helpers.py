import requests
import pandas as pd
import numpy as np 
from pyarrow import fs
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.stats import zscore
import matplotlib.pyplot as plt
from tqdm import tqdm


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


def get_absent_lat_lon_from_gouv_api(df):
    empties = df[df["lon_gare"].isna()].copy()
    base_url = "https://api-adresse.data.gouv.fr/search/"
    # Paramètres de la requête
    params = {"q": "", "limit": 1}
    i = 0
    for idx, row in empties.iterrows():
        params["q"] = "gare de " + row["nom_gare"]
        response = requests.get(base_url, params=params)
        try:
            data = response.json()
            coordinates = data["features"][0]["geometry"]["coordinates"]
            i = i + 1
        except:
            coordinates = [None, None]
        df.loc[idx, "lon_gare"] = coordinates[0]
        df.loc[idx, "lat_gare"] = coordinates[1]
    print(i, "absent addresses filled successfully")
    return df

def fill_regional_stat_with_lat_lon(regional_stat):

  base_url = "https://api-adresse.data.gouv.fr/search/"
  # Paramètres de la requête
  params = {"q": "", "limit": 1}
  i = 0
  for idx, row in tqdm(regional_stat.iterrows(), desc="Processing"):
   
     params["q"] = f"{row["nomcommune"]} {row["codecommune"]}"
     response = requests.get(base_url, params=params)
     try :
         data = response.json()
         coordinates = data["features"][0]["geometry"]["coordinates"]
         i = i + 1
     except:
         coordinates = [None, None]
     regional_stat.loc[idx, "lon"] = coordinates[0]
     regional_stat.loc[idx, "lat"] = coordinates[1]
  return regional_stat

def delete_outliers_z_score(df, series):
    df["z_score"] = zscore(series)
    no_outliers_table = df[df["z_score"].abs() < 3]

    print("nb removed observations : ", df.shape[0] - no_outliers_table.shape[0])
    no_outliers_table = no_outliers_table.drop("z_score", axis=1)
    return no_outliers_table


def plot_hist(series, title_suffix=""):

    plt.figure(figsize=(3, 2))
    plt.hist(series, bins=50, edgecolor="black")
    plt.title(f"Histogram of {series.name} {title_suffix}", fontsize=14)
    plt.xlabel(series.name, fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.grid(axis="y", linestyle="--")
    plt.show()


def simple_plot_map(lat,lon):
    plt.scatter(lon, lat, s=1, color="black")
    plt.title("Stations in France")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()


class s3_connection():
    def __init__(self,directory):
        try:
         s3 = fs.S3FileSystem(endpoint_override="https://" + "minio.lab.sspcloud.fr")
         s3.get_file_info(fs.FileSelector(directory, recursive=True))
         print("connection successful")
        except:
         s3="connection not established, debug "
         print(s3)
        self.s3=s3
     
    def from_json_to_parquet_store_in_s3(self,json_table, directory):
      table = pa.Table.from_pylist(json_table)
      pq.write_table(table, directory, filesystem=self.s3)
  
    def from_pandas_to_parquet_store_in_s3(self,df, directory):
      table = pa.Table.from_pandas(df)
      pq.write_table(table, directory, filesystem=self.s3)
   
    def get_tables_from_s3(self,directory):
        df = pq.ParquetDataset(directory, filesystem=self.s3).read_pandas().to_pandas()
        return df
    

def haversine_vectorized(lat1, lon1, lat2, lon2):
    """ 
    
    References
    ---------

    https://www.movable-type.co.uk/scripts/latlong.html
    https://www.igismap.com/haversine-formula-calculate-geographic-distance-earth/
    """
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = np.radians([lat1, lon1, lat2, lon2])
    # Haversine formula from ressources
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.atan2(np.sqrt(a), np.sqrt((1-a)))
    r = 6371  # Radius of Earth in kilometers
    return c * r #dist in km 