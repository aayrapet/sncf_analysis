import requests
import pandas as pd
import numpy as np 
import s3fs
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

def delete_outliers_z_score(df, series):
    df["z_score"] = zscore(series)
    no_outliers_table = df[df["z_score"].abs() < 3]

    print("nb removed observations : ", df.shape[0] - no_outliers_table.shape[0])
    no_outliers_table = no_outliers_table.drop("z_score", axis=1)
    return no_outliers_table



def simple_plot_map(lat,lon):
    plt.scatter(lon, lat, s=1, color="black")
    plt.title("Stations in France")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()



def calculate(
    df: pd.DataFrame,
    group,
    fields,
    stats,
    names
) -> pd.DataFrame:
    
    """
    "Group by" operation on multiple fields and aggregate functions, the code becomes easier than standard pandas writing

    Args:
        df (DataFrame): DataFrame
        group : Aggregation column/columns
        fields: Calculation column/columns, on which aggregation function will be applied
        stats: Function/functions applied on fields
        names: Column name/names of new calculated columns

    Returns:
        DataFrame: Aggregated DataFrame by columns "group", with functions defined in "stats" on columns defined in "fields"

    Example:
        'Calculate number of clients by boutique
        calculate(my_dataframe,group=["boutique_name"],fields=["individuid"],stats=["nunique"],names=["nb_of_clients"])

        'Calculate number of clients by boutique, TO, nb of visits
        calculate(my_dataframe,group=["boutique_name","fsh_advisor"],fields=["individuid","price","purchase_date"],stats=["nunique","sum","nunique"],names=["nb_of_clients","Turnover","nb_of_visits])
    https://github.com/florazhg/NLP-Project/blob/main/main_nb_w_topic.ipynb
    
    """

    no_names_introduced=False
    if names is None:
        no_names_introduced=True
        names = fields
    table = None

    #calculer pour chaque couple des variables et statistiques 
    #une des limites: ne pas utiliser les mêmes variables dans groupe et field
    for field, stat,name in zip(fields, stats,names):
        if name==None or no_names_introduced:
            name=f"{field}_{stat}"
   
        v = (
            df.groupby(group)[field]
            .agg(stat)
            .reset_index()
            .rename(columns={field: name})
        )

        if table is None:
            table = v
        else:
            table = table.merge(v, on=group, how="left")

    return table


def plot_hist(ax, series, title_suffix=""):
    ax.hist(series, bins=50, edgecolor="black")
    ax.set_title(f" {series.name} {title_suffix}", fontsize=14)
    ax.set_xlabel(series.name, )
    ax.set_ylabel("Frequency", )
    ax.grid(axis="y", linestyle="--")

def plot_map_with_legend(ax, lon, lat, categorical_continuos,suffix_description):
   scatter = ax.scatter(
       lon, 
       lat, 
       s=10,  # Increase size for visibility
       c=categorical_continuos,  # Color based on number of passengers
       cmap='viridis_r'  # Use a perceptible color map
   )
   cbar = plt.colorbar(scatter, ax=ax)  # Add color legend
   cbar.set_label(suffix_description)
   ax.set_title("Stations by "+suffix_description)
   ax.set_xlabel("Longitude")
   ax.set_ylabel("Latitude") 



class s3_connection():
    def __init__(self):
        try:
         s3 = s3fs.S3FileSystem(client_kwargs={"endpoint_url": "https://minio.lab.sspcloud.fr"})
         
         print("connection successful")
        except:
         s3="connection not established, debug "
         print(s3)
        self.s3=s3
    
    def from_pandas_to_parquet_store_in_s3(self,df, directory):
      with self.s3.open(directory, "wb") as file_out:
        df.to_parquet(file_out)
      
    
    def get_tables_from_s3(self,directory):
        with self.s3.open(directory, "rb") as file_in:
          df = pd.read_parquet(file_in)
        return df
    
    def read_csv_from_s3(self, directory, columns_to_select=None, dtype_spec=None):
        with self.s3.open(directory, "rb") as file_in:
            df = pd.read_csv(file_in, usecols=columns_to_select, dtype=dtype_spec)
    
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