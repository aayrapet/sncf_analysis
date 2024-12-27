
import pandas as pd
import numpy as np 
import s3fs
from scipy.stats import zscore

def delete_outliers_z_score(df, series):
    df["z_score"] = zscore(series)
    #assuming normal distribution so series have to be in log !!
    no_outliers_table = df[df["z_score"].abs() < 3]

    print("nb removed observations : ", df.shape[0] - no_outliers_table.shape[0])
    no_outliers_table = no_outliers_table.drop("z_score", axis=1)
    return no_outliers_table

def calculate(df: pd.DataFrame, group, fields_stats_names) -> pd.DataFrame:

    table = None

    # calculer pour chaque couple des variables et statistiques
    # une des limites: ne pas utiliser les mêmes variables dans groupe et field
    for field_stat_name in fields_stats_names:
        field, stat = field_stat_name[0], field_stat_name[1]
        try:
            name = field_stat_name[2]
        except:
            name = f"{field}_{stat}"

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
      try:
        with self.s3.open(directory, "wb") as file_out:
         df.to_parquet(file_out)
      except: 
        print("Cher lecteur, cette fonction écrit dans le dossier spécifié, mais vous n'avez pas les droits :( ")
      
    
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