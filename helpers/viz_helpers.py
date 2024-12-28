import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scipy.stats import f_oneway


def simple_plot_map(lat,lon):
    """
    plot les gares sur la carte juste 
    """
    plt.scatter(lon, lat, s=1, color="black")
    plt.title("Stations in France")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()


def corr_matrix(df,filter_include=None,filter_exclude=None,figsize=(10,6)):
  """
  plot matrice de correlation pearson entre les variables continues
  """
  numeric_columns = df.select_dtypes(include=[np.number])
  if filter_exclude:
    numeric_columns=numeric_columns.drop(filter_exclude,axis=1)
  correlation_matrix = numeric_columns.corr()
  if filter_include:
    correlation_matrix=correlation_matrix[correlation_matrix.index.isin(filter_include)]
  #init graph
  plt.figure(figsize=figsize)
  #heatmap of corr matrix results
  sns.heatmap(
      correlation_matrix,
      #style
      annot=True,
      fmt=".2f",
      cmap="coolwarm",
      cbar=True,
      vmin=-1, vmax=1,
      linewidths=.5,  
      linecolor='gray'  
  )
  
  plt.title("Pearson Correlation Matrix ")
  plt.xticks(rotation=45, ha='right')  #Rotate 45 degrees
  plt.yticks(rotation=0)  #Keep y horizontal
  plt.tight_layout()  
  plt.show()




def analysis_between_continous_and_categorical_var(df,category_var,interest_var,figsize=(12, 6)):

   """
   plot boxplot, faire anova, tukey
   """
   #---------------VIZ PART--------------------------
   #-------------------------------
   plt.figure(figsize=figsize)  # Adjust figure size
   sns.boxplot(
       data=df,
       x=category_var  ,               # Your DataFrame
       hue=category_var, 
                     # Categorical variable
       y=interest_var,  # Continuous variable
       palette='Set2'   ,
       legend=False          # Optional: Color palette
   )
   
   # Rotate x-axis labels for better visibility
   plt.xticks(rotation=45)
   plt.title("Box Plot of Total Voyagers by Region")
   plt.xlabel("Regions")
   plt.ylabel("Total Voyagers (2022)")
   
   plt.tight_layout()
   plt.show()

   #---------------ANOVA TEST--------------------------
   #-------------------------------

   #cette partie suppose les données normales

   #filtrer par catégorie et extraire pour chaque catégorie le nb de voyageurs
   groups = [table[interest_var].values for region_filter, table in df.groupby(category_var)]
   #faire anova avec *, car c'est un requis de la fonction (args) 
   f_stat, p_value = f_oneway(*groups)
   print(f"P-value: {p_value:.4f}")
      
   if p_value < 0.05:
       print("Rejeter l'hypothèse nulle : Au moins une moyenne de groupe est différente.")
   else:
       print("Ne pas rejeter l'hypothèse nulle : Les moyennes des groupes ne sont pas significativement différente")
   print("-----------------------------------------")

   #---------------TUCKEY POST HOC TEST--------------------------
   #-------------------------------


   tukey = pairwise_tukeyhsd(endog=df[interest_var], groups=df[category_var], alpha=0.05)
   #supprimer les colonnes redondantes et avoir une belle table data frame
   tukey_summary = pd.DataFrame(
       data=tukey._results_table.data[1:],
       columns=tukey._results_table.data[0]  
   ) 
   nb_couples=tukey_summary[tukey_summary['reject'] == True].shape[0]
   print(nb_couples," combinaisons des catégories sont significativement différentes")

   

def plot_hist(ax, series, title_suffix=""):

    """ 
    pour une axe plot hist

    """
    ax.hist(series, bins=50, edgecolor="black")
    ax.set_title(f"{series.name} {title_suffix}", fontsize=14)
    ax.set_ylabel("Frequency")
    ax.grid(axis="y", linestyle="--")

def plot_scatter(ax, x_series, y_series, color='blue', alpha=0.7, edgecolor='k'):
    """ 
    pour une axe plot scatter

    """
    ax.scatter(x_series, y_series, color=color, edgecolor=edgecolor, alpha=alpha)
    ax.set_xlabel(x_series.name)
    ax.set_ylabel(y_series.name)
    ax.grid(True, linestyle="--", alpha=0.5)

def plot_map_with_legend(ax, lon, lat, categorical_continuos, suffix_description):
    """ 
    pour une axe plot map

    """
    scatter = ax.scatter(
        lon, 
        lat, 
        s=10,  
        c=categorical_continuos,  
        cmap='viridis_r'  
    )
    cbar = plt.colorbar(scatter, ax=ax)  
    cbar.set_label(suffix_description)
    ax.set_title(f"Stations by {suffix_description}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


def plot_square(
    fields_names,
    plot_type="hist",
    figsize=(13, 7),
    columns=3,
    lat=None,
    lon=None,
):
    """
    Une fonction unifiée pour créer une grille de sous-graphiques et appeler
    la fonction de traçage appropriée (histogramme/nuage de points/carte) en fonction de plot_type.

    Paramètres
    ----------
    fields_names : list
        - Pour plot_type="hist":
            Chaque élément : [série, suffixe_titre (optionnel)]
        - Pour plot_type="scatter":
            Chaque élément : [x_series, y_series]
        - Pour plot_type="map":
            Chaque élément : [catégorique_continu, description_suffixe]
    plot_type : str
        Une des options {"hist", "scatter", "map"}.
    figsize : tuple
        Taille de la figure transmise à plt.subplots.
    columns : int
        Nombre de colonnes dans chaque ligne de la figure.
    lat : array-like
        Valeurs de latitude (utilisé uniquement si plot_type="map").
    lon : array-like
        Valeurs de longitude (utilisé uniquement si plot_type="map").
"""

    len_fields = len(fields_names)
    nb_axis = int(np.ceil(len_fields / columns))

    fig, axs = plt.subplots(nb_axis, columns, figsize=figsize)
    axs = axs.flatten()  # Flatten for easier iteration

    for idx, el in enumerate(fields_names):
        ax = axs[idx]
        
        if plot_type == "hist":
            series = el[0]
            #juste pour le suffix custom s'assurer que bien present
            title_suffix = el[1] if len(el) > 1 else ""


            plot_hist(ax, series, title_suffix=title_suffix)##

        elif plot_type == "scatter":
            x_series = el[0]#
            y_series = el[1]
            plot_scatter(ax, x_series, y_series)

        elif plot_type == "map":
            if lat is None or lon is None:
                raise ValueError("lat and lon must be provided for plot_type='map'")
            field = el[0]
            suffix_description = el[1]
            plot_map_with_legend(ax, lon, lat, field, suffix_description)

        else:
            raise ValueError(f"Unknown plot_type: '{plot_type}'")

    #il faut dedupliquer les legendes
    for ax in axs[len_fields:]:
        ax.axis("off")

    plt.tight_layout()
    plt.show()