import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt


def simple_plot_map(lat,lon):
    plt.scatter(lon, lat, s=1, color="black")
    plt.title("Stations in France")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()



def plot_hist(ax, series, title_suffix=""):
    ax.hist(series, bins=50, edgecolor="black")
    ax.set_title(f" {series.name} {title_suffix}", fontsize=14)
    ax.set_xlabel(series.name, )
    ax.set_ylabel("Frequency", )
    ax.grid(axis="y", linestyle="--")

def plot_scatter(ax, x_series, y_series, color='blue', alpha=0.7, edgecolor='k'):

    ax.scatter(x_series, y_series, color=color, edgecolor=edgecolor, alpha=alpha)
    
    ax.set_xlabel(x_series.name)
    ax.set_ylabel(y_series.name)
    ax.grid(True, linestyle="--", alpha=0.5)

def corr_matrix(df,filter_include=None,filter_exclude=None,figsize=(10,6)):
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

def plot_square_map(lat,lon,fields_names,  figsize=(28, 28)):
    len_fields=len(fields_names)
    nb_axis=int(np.ceil(len_fields / 3))#i want 3 columns in every row
    fig, axs = plt.subplots(nb_axis, 3, figsize=figsize) 
    axs = axs.flatten()  # Flatten for easier iteration
    for idx, el in enumerate(fields_names):
        field = el[0]
        name = el[1]
        ax = axs[idx]  # Select the correct subplot
        #use another function
        plot_map_with_legend(
            ax,
            lon,
            lat,
            field,
            suffix_description=name,
        )
    #delete duplicated legends
    for ax in axs[len(fields_names):]:
        ax.axis("off") 
    plt.show()