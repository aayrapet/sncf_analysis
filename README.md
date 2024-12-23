# Projet Python pour la data science

## 0. Présentation

*Ce projet a été réalisé dans le cadre du cours "Python pour la data science" de l'ENSAE*

Le train est perçu comme le mode de transport de demain : il est écologique, il est relativement rapide et il est de plus en plus utilisé.

Notre but est de trouver les déterminants de la fréquentation des gares SNCF en France à partir de données communales à notre disposition : nombre d'habitant, catégories socio-professionnelles, taux de diplôme, fréquentation des gares et la distance de la gare la plus proche. Cela a pour objectif de déterminer si rouvrir des gares de certaines communes pourrait attirer des personnes en fonction des variables de notre modèle. 

Notre projet se décompose en 3 parties :
- Extraction des données 
- Visualisation des données 
- Le modèle

Les packages utilisés sont mentionnés dans le fichier "helpers.py".

## 1. Extraction des données

Les données ont été recueillies à partir des API de la SNCF afin d'extraire les données de localisation des communes et des fréquentations des gares SNCF.

Une fois ces données extraites, on les fusionne avec les données communales recueillies à partir de fichiers sur le web. Ces données comportent par commune ;
- le taux moyen de personnes diplômées
- le taux de personnes appartenant à certaines catégories socio-professionnelles
- le nombre d'habitant par commune

Attention ! Certaines lignes consistent à exporter des tables, seules la personnes qui détient le bucket peut écrire, cette étape a été faite au préalable pour obtenir la table finale.

## 2. Visualisation des données

La visualisation consiste à plot les gares sur une carte de France.

Nous avons décidé d'enlever les valeurs aberrantes de fréquentation des gares (Quelques dizaines de voyageurs et la gare du Nord à Paris)

Enfin, nous avons repris la carte de France avec les points représentant les gares, en ajoutant des couleurs en fonction d'autres caractéristiques comme la population de la commune ou la région.

## 3. Le modèle

Avec ces données, nous commençons à percevoir un lien entre revenu de la commune et la fréquentation des gares, mais est-ce réellement le cas ? Pour répondre à la question, nous utilisons le modèle de régression linéaire des moindres carrés ordinaires. 

En introduisant les variables socio-économiques, du taux de diplôme par commune et de la population de la commune, le revenu n'est plus statistiquement significatif. En revanche les catégories socio-professionnelles le sont. On peut aussi en déduire qu'il existe un lien positif entre la distance de la gare la plus proche et le nombre de voyageurs d'une gare donnée, ce qui semble confirmer notre hypothèse : une gare située plus loin attire davantage de voyageurs. 

Le modèle présente néanmoins des failles. Il existe d'autres variables qui peuvent avoir un effet sur la fréquentation des gares, telles que la densité de population ou le nombre de train qui passent par jour par exemple. Ces données pourraient êtres estimées mais elles ne le sont pas dans ce projet. Les données de fréquentation des gares sont des données agrégées et cachent les différences au sein des types de trains qui y sont pris (TGV, Intercités, TER). Ce ne sont pas les mêmes personnes qui prennent le TER et le TGV. Il est donc difficile d'en déduire un modèle causal, il faudrait pour cela rajouter des variables. 


comment utiliser (premiere etape pip install -r "requirements.txt" et apres main.ipynb )

pip install 
!pip install pyopenssl --upgrade 