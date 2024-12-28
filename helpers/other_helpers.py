
import pandas as pd
import numpy as np 
import math as mt
import s3fs
from scipy.stats import zscore
import statsmodels.api as sm



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



def is_decrease(vector: list) -> bool:
        """
        This function is used for model selection using Information Criteria (IC)
        For this, we will observe only two last values of the list. The selection algorithm will have 3 rules:

        1.iF N-1 value > N value then continue the algorithm so the function will return True
        2.if there is no values yet in the list, so we work with initialised vector so the function will return True to start accuulating IC
        3.if the lenght of the function is 1 return True to get more IC for model comparison

        once N-1 value<N value the function returns False, the algorithm stops -> we get our final model that minimses IC


        """
        val = False
        if not vector:
            val = True
        elif len(vector) == 1:
            val = True
        elif len(vector) >= 2:
            if (vector[len(vector) - 2] - vector[len(vector) - 1]) > 0:
                val = True
        return val

def delete_i_from_index(exclusion: int, vector: np.ndarray) -> np.ndarray:
        """

        Simple function just to exclude observation from numpy array
        exclusion: digit to exclude
        vector: exclude from this numpy array this digit


        """
        new_index = []
        for i in range(len(vector)):
            if vector[i] != exclusion:
                new_index.append(vector[i])
        return new_index


def stepwise_selection(
        
        x: np.ndarray,
        y: np.ndarray,
        aic
    ) -> np.ndarray:
        """
        Stepwise selection Algorithm

        Starts with  model filled with 50% of variables selected randomly (inside vars),
        other 50% are kept outside the model (outide vars).

        Tries to remove variables from inside vars doing backward regression
        on them-> calculates the min IC and respective inside var

        At the same time tries to add variables to inside vars doing forward regression
        and calculates minimal IC and respective inside var.

        The alg will drop the variable if min IC backward < min IC forward and vice versa.
        Very important: when the variable is removed, it does not leave the model forever,
        it will go outside vars so that we leave the possibility to this var to get back later.

        Parameters
        ------
        Class_algorithm (class) : parametric model on which variable selection will be performed
        x (array alike) : matrix of x variables
        y (array alike) : vector of y
        criterion (str) : Information criterion (IC) that is a stopping criterion that stops

                For linear regression accepted are:
                                     -BIC_ll |AIC_ll |AIC_err |BIC_err |LL
                For logistic regression accepted are:
                                     -BIC_ll |AIC_ll |LL because we cant calculate errors


        Code originates from my ML project : 
        https://github.com/aayrapet/ml_parametric/blob/main/_autoselect.py

        """

        # make sure that during code excecution we dont store the process of this function

        x=np.array(x)
        y=np.array(y)
        v = np.random.permutation(x.shape[1])
        split_index = mt.floor(x.shape[1] / 2)
        index = v[0:split_index]
        remaining_index = v[split_index:]

        min_aic = []
        first_iteration = True

        while is_decrease(min_aic):
            if first_iteration:

                first_iteration = False

            else:
                if min_remove_criterion < min_add_criterion:
                    index = delete_i_from_index(index_found_remove, index)
                    remaining_index = np.hstack((remaining_index, index_found_remove))
                else:
                    remaining_index = delete_i_from_index(
                        index_found_add, remaining_index
                    )
                    index = np.hstack((index, index_found_add))

            start = float("inf")
            first_time = True
            # /*BACKWARD regression*/
            if len(index) != 0:
                for i in range(-1, len(index)):
                    if first_time:
                        new_index = index.copy()
                        first_time = False

                    else:
                        new_index = delete_i_from_index(index[i], index)

                    r=sm.OLS(y,sm.add_constant(x[:,new_index])).fit(cov_type='HC3')
                    this_criterion=r.aic if aic=="aic" else r.bic

                

                    if start > this_criterion:
                        start = this_criterion
                        
                        index_found_remove = index[i]

                min_remove_criterion = start.copy()
            else:
                # if vector is empty so just do forward selection because min_add_criterion will be  < min_remove_criterion
                min_remove_criterion = min_add_criterion + 1

            # /*FORWARD regression*/

            start = float("inf")
            # /* do all candidates for inclusion (if they still remain) */
            if len(remaining_index) != 0:
                for i in range(len(remaining_index)):

                    new_index = np.hstack((index, remaining_index[i]))

                    r=sm.OLS(y,sm.add_constant(x[:,new_index])).fit(cov_type='HC3')
                    this_criterion=r.aic if aic=="aic" else r.bic

                    if start > this_criterion:
                        start = this_criterion.copy()
                        index_found_add = remaining_index[i]

                min_add_criterion = start.copy()

            else:
                # if vector is empty so just do backward selection because min_remove_criterion will be  < min_add_criterion
                min_add_criterion = min_remove_criterion + 1

            if min_remove_criterion < min_add_criterion:
                min_aic.append(min_remove_criterion)
            else:
                min_aic.append(min_add_criterion)

        
        return np.array(index)