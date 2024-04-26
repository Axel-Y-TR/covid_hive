import pandas as pd
import happybase

connection = happybase.Connection('localhost')

df_confirmed = pd.read_csv('C:/Users/vmazabraud/Documents/Cour/covid_hive/data/time_series_covid19_confirmed_global.csv')
df_deaths = pd.read_csv('C:/Users/vmazabraud/Documents/Cour/covid_hive/data/time_series_covid19_deaths_global.csv')
df_recovered = pd.read_csv('C:/Users/vmazabraud/Documents/Cour/covid_hive/data/time_series_covid19_recovered_global.csv')

data_columns = df_confirmed.columns
country_columns = data_columns[:4]
date_columns = data_columns[4:]

df_confirmed_unpivoted = df_confirmed.melt(id_vars=country_columns, var_name='date', value_name='confirmed')
df_deaths_unpivoted = df_deaths.melt(id_vars=country_columns, var_name='date', value_name='deaths')
df_recovered_unpivoted = df_recovered.melt(id_vars=country_columns, var_name='date', value_name='recovered')

df_concatenated = pd.concat([df_confirmed_unpivoted, df_deaths_unpivoted['deaths'], df_recovered_unpivoted['recovered']], axis=1)

df_concatenated.drop('Province/State', axis=1, inplace=True)
df_concatenated = df_concatenated.fillna(0)
df_concatenated['date'] = pd.to_datetime(df_concatenated['date'])

# Définir une fonction pour insérer les données dans HBase
def insert_row(row, table):
    row_key = str(row.name)  # Utiliser l'index de la ligne comme clé de ligne
    data = {
        b'info:Country/Region': str(row['Country/Region']).encode(),
        b'info:date': str(row['date']).encode(),
        b'info:Lat': str(row['Lat']).encode(),
        b'info:Long': str(row['Long']).encode(),
        b'info:confirmed': str(row['confirmed']).encode(),
        b'info:deaths': str(row['deaths']).encode(),
        b'info:recovered': str(row['recovered']).encode()
    }
    table.put(row_key.encode(), data)
 
# Vérification de l'existence de la table
try:
    column_family = 'info'
    if b'covid_table' not in connection.tables():
        print("La table 'covid_table' n'existe pas, création...")
        connection.create_table(
            'covid_table',  # Nom de la table
            {column_family: dict()}  # Spécifiez la famille de colonnes
        )
 
    # Insertion des données dans la table
    with connection.table(b'covid_table').batch(batch_size=1000) as table:
        df_concatenated.apply(insert_row, args=(table,), axis=1)
        print("Insertion des données terminée")
 
finally:
    if 'connection' in locals():
        connection.close()  # Fermeture de la connexion à la base de données
