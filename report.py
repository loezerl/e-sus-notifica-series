"""
Autor - Lucas Loezer (loezer.lucas@gmail.com)



As credenciais desse script são de domínio publico. A própria página da API disponibliza
usuário e senha para que seja possível acessar os dados:
e-SUS Notifica: 
https://opendatasus.saude.gov.br/dataset/casos-nacionais/resource/30c7902e-fe02-4986-b69d-906ca4c2ec36

Esse script apenas facilita a comunicação com a API fazendo queries server-side para construir um arquivo de série temporal.
As informações por dia calculadas são:
- Quantidade de RT-PCR positivos.
- Quantidade de RT-PCR negativos.
- Quantidade de RT-PCR positivos nas faixas etárias:
    [0, 4], [5, 9], [10, 14], [15, 19]
    [20, 29], [30, 39], [40, 49], [50, 59]
    [60, 69], [70, 79], [80, 999]
- Quantidade de óbitos para RT-PCR positivos.

Para quaisquer dúvidas, não hesite em me contatar por e-mail.
"""

"""
GLOBAL VARS
"""
USERNAME = "user-public-notificacoes"
PASSWRD = "Za4qNXdyQNSa9YaA"
AUTH = (USERNAME, PASSWRD)

## SIZE = 0 não retornar os hits dos documentos, mas retorna o aggregation completo.
QUERY_SIZE = 0

ESTADOS = [
  'sp', 'pr', 'sc', 'rs',
  'ms', 'ro', 'ac', 'am',
  'rr', 'pa', 'ap', 'to',
  'ma', 'rn', 'pb', 'pe',
  'al', 'se', 'ba', 'mg',
  'rj', 'mt', 'go', 'df',
  'pi', 'ce', 'es',
]

REGIOES = {
  "norte": ['ac', 'ap', 'am', 'pa', 'ro', 'rr', 'to'],
  "nordeste": ['al', 'ba', 'ce', 'ma', 'pb', 'pe', 'pi', 'rn', 'se'],
  "centro-oeste": ['go', 'mt', 'ms', 'df'],
  "sudeste": ['es', 'mg', 'rj', 'sp',],
  "sul": ['pr', 'rs', 'sc'],
}

sort = [
  {"dataNotificacao": {"order": "asc"}}
]

FAIXAS_ETARIAS = [
  [0, 4], [5, 9], [10, 14],
  [15, 19], [20, 29], [30, 39],
  [40, 49], [50, 59], [60, 69],
  [70, 79], [80, 999]
]

import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
import json
import argparse


parser = argparse.ArgumentParser(
    description='Esse script tem como funcionalidade se conectar na API e-SUS Notifica e gerar um relatório ordenado temporalmente \
      com informações sobre os testes RT-PCR positivos e negativos divididos por faixa etária. \
        Autor - Lucas Loezer (loezer.lucas@gmail.com)')
parser.add_argument('-r', type=str, help="Região. Caso queira extrair a informação de uma região do Brasil. Valores possiveis: norte, nordeste, centro-oest, sudeste e sul.", default="")
parser.add_argument('-e', type=str, help="Estado. Informe as siglas dos estados separado por vírgula. Caso não seja informado o relatório \
  estará contabilizando todos os estados brasileiros.", default="")
parser.add_argument('-m', type=str, help="Município. Informe o nome do município, caso não seja informado o relatório \
  estará contabilizando todos os municípios do estado.", default="")
parser.add_argument('-g', type=str, help="Intervalo de agrupamento. Informe se os dados serão agrupados por dia (day) ou mês (month)", default="day")
parser.add_argument('-f', help="Formato de saída do relatório: [xlsx] ou [csv]", default='xlsx')
parser.add_argument('-o', type=str, help="Nome do arquivo de saída. Não é preciso informar o tipo de saída.", default="Relatorio")
args = parser.parse_args()

ESTADO = args.e.lower()
MUNICIPIO = args.m
ORDEM_AGG = args.g
OUTPUT_FILE = args.o
OUTPUT_FILE_FORMAT = args.f
PAIS_FLAG = False
MUNICIPIO_FLAG = False
ESTADOS_FLAG = False
REGIAO = args.r.lower()

ESTADOS_LISTADOS = [e for e in ESTADO.split(",") if e != ""]

for e in ESTADOS_LISTADOS:
  if (e != "") and (e not in ESTADOS):
    raise Exception("Sigla de estado não reconhecida.")

if ORDEM_AGG not in ['day', 'month']:
  raise Exception("Valor de intervalo de agrupamento inválido! Informe se o agrupamento será por dia [day] ou mês [month]. O valor default é por dia.")

if OUTPUT_FILE_FORMAT not in ['csv', 'xlsx']:
  raise Exception("Formato de arquivo de saída inválido! Informe se o formato será CSV [csv] ou EXCEL [xlsx].")

if len(ESTADOS_LISTADOS) > 1 and MUNICIPIO != "":
  raise Exception("Parâmetros inválidos! Não é possível gerar o relatório para mais de um estado e um município.")

if REGIAO != "":
  if not (REGIAO in REGIOES):
    raise Exception("Região inválida! Caso queira extrair o relatório por região brasileira, informe um dos valores: norte, nordeste, sul, sudeste e centro-oeste.")
  else:
    ESTADOS_LISTADOS = REGIOES[REGIAO]

if len(ESTADOS_LISTADOS) > 1:
  print("Realizando a análise para os estados: ")
  print(ESTADOS_LISTADOS)
  ESTADOS_FLAG = True
  estado_str = ""
  for e in ESTADOS_LISTADOS:
    estado_str += f"{e}-"
  estado_str = estado_str[:-1] 
  OUTPUT_FILE = f"{OUTPUT_FILE}_Estados_{estado_str}"
elif len(ESTADOS_LISTADOS) <= 0:
  print("Realizando a análise para todos os Estados.")
  PAIS_FLAG=True
  OUTPUT_FILE = f"{OUTPUT_FILE}_BRASIL"
elif len(ESTADOS_LISTADOS) == 1 and MUNICIPIO != "":
  print(f"Realizando a análise para {MUNICIPIO}/{ESTADO}")
  OUTPUT_FILE = f"{OUTPUT_FILE}_{ESTADO}_{MUNICIPIO}"
  MUNICIPIO_FLAG = True
elif len(ESTADOS_LISTADOS) == 1:
  print(f"Realizando a análise para o estado {ESTADO}")
  OUTPUT_FILE = f"{OUTPUT_FILE}_{ESTADO}"
  MUNICIPIO_FLAG = False
else:
  raise Exception("Opção inválida.")

BASE_URL_PAIS = "https://elasticsearch-saps.saude.gov.br/desc-esus-notifica-estado-"

aggs = {
  "group_by_date":{
    "date_histogram": {
      "field": "dataNotificacao",
      "interval": ORDEM_AGG
    }
  }
}


pcr_positivo_ranges = {}
for f in FAIXAS_ETARIAS:
  pcr_positivo_ranges["pcr-positivo-{}a{}".format(f[0], f[1])] = {}
  if MUNICIPIO_FLAG:
    pcr_positivo_ranges["pcr-positivo-{}a{}".format(f[0], f[1])]['query_string'] = {
      "query": f"_exists_:resultadoTeste AND (Positivo) AND tipoTeste:(RT-PCR) AND municipio:({MUNICIPIO}) AND idade:(>={f[0]}) AND idade:(<={f[1]}) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
      "default_field": "resultadoTeste"
    }
  else:
    pcr_positivo_ranges["pcr-positivo-{}a{}".format(f[0], f[1])]['query_string'] = {
      "query": f"_exists_:resultadoTeste AND (Positivo) AND tipoTeste:(RT-PCR) AND idade:(>={f[0]}) AND idade:(<={f[1]}) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
      "default_field": "resultadoTeste"
    }

querys = {}
if MUNICIPIO_FLAG:
  querys["pcr-positivo"] = {}
  querys["pcr-positivo"]["query_string"] = {
      "query": f"_exists_:resultadoTeste AND (Positivo) AND tipoTeste:(RT-PCR) AND municipio:({MUNICIPIO}) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
      "default_field": "resultadoTeste"
  }
  querys["pcr-negativo"] = {}
  querys["pcr-negativo"]["query_string"] = {
    "query": f"_exists_:resultadoTeste AND (Negativo) AND tipoTeste:(RT-PCR) AND municipio:({MUNICIPIO}) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
    "default_field": "resultadoTeste"
  }
else:
  querys = {
      "pcr-positivo": {
        "query_string":{
          "query": "_exists_:resultadoTeste AND (Positivo) AND tipoTeste:(RT-PCR) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
          "default_field": "resultadoTeste"
        }
      },
      "pcr-negativo": {
        "query_string": {
          "query": "_exists_:resultadoTeste AND (Negativo) AND tipoTeste:(RT-PCR) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
          "default_field": "resultadoTeste"
        }
      }
  }

for k in pcr_positivo_ranges:
  querys[k] = pcr_positivo_ranges[k]

if MUNICIPIO_FLAG:
  querys["obitos"] = {
    "query_string": {
          "query": f"_exists_:resultadoTeste AND (Positivo) AND tipoTeste:(RT-PCR) AND municipio:({MUNICIPIO}) AND evolucaoCaso:(Óbito) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
          "default_field": "resultadoTeste"
    }
  }
else:
  querys["obitos"] = {
    "query_string": {
          "query": "_exists_:resultadoTeste AND (Positivo) AND tipoTeste:(RT-PCR) AND evolucaoCaso:(Óbito) AND dataNotificacao:[2020-01-01T00:00:00.000Z TO *]",
          "default_field": "resultadoTeste"
    }
  }

headers = {
  "Content-Type": "application/json"
}

import time
start_time = time.time()

if ESTADOS_FLAG:
  ESTADOS = ESTADOS_LISTADOS
elif not PAIS_FLAG:
  ESTADOS = [ESTADO]

FIRST_TIME = True
for estado in ESTADOS:
  print(f"== Acessando os dados do estado: [{estado}] ==")
  URL = BASE_URL_PAIS + f"{estado}/_search?pretty"
  dataframes = []
  for query_id in querys:
      query = {
        "query": querys[query_id],
        "sort": sort,
        "aggs": aggs,
        "size": QUERY_SIZE
      }
      query_time = time.time()
      response = requests.request("GET", URL, headers = headers, auth=(USERNAME, PASSWRD), data = json.dumps(query))
      json_resp = json.loads(response.text)
      print("Query [{}] | Tempo: {:.3f} segundos".format(query_id, (time.time() - query_time)))
      rows = []
      if response.status_code != 200:
        raise Exception("Não retornou sucesso na query! Razão: " + str(json_resp))
      try:
        for el in json_resp['aggregations']['group_by_date']['buckets']:
            rows.append({"Data": el['key_as_string'], query_id: el['doc_count']})
      except Exception as e:
        raise Exception("Query possivelmente inválida! Verifique se os dados parametrizados estão corretos. Razão: " + str(e))

      df_q = pd.DataFrame(rows)
      if len(df_q.index) != 0:
        df_q.replace(np.nan, 0, inplace=True)
        df_q["Data"] = (pd.to_datetime(df_q["Data"], format="%Y-%m-%d")).dt.date
        dataframes.append(df_q)
      else:
        print(f"\tQuery {query_id} sem retorno. Não será incluída no relatório final!")
  if FIRST_TIME:
    df = dataframes[0]
    for d in dataframes[1:]:
      df = pd.merge(left=df, right=d, left_on=['Data'], right_on=['Data'], how='left')
    FIRST_TIME = False
  else:
    df_estado = dataframes[0]
    for d in dataframes[1:]:
      df_estado = pd.merge(left=df_estado, right=d, left_on=['Data'], right_on=['Data'], how='left')
    df = pd.concat([df, df_estado], axis=0)
    
  print(f'Estado [{estado}] processado.\n')

if PAIS_FLAG or ESTADOS_FLAG:
  df = df.groupby(by=['Data'], as_index=False).agg('sum')
  df.sort_values(by='Data', inplace=True)

if OUTPUT_FILE_FORMAT == "xlsx":
  df.to_excel(f'{OUTPUT_FILE}.{OUTPUT_FILE_FORMAT}', index=False)
elif OUTPUT_FILE_FORMAT == "csv":
  df.to_csv(f'{OUTPUT_FILE}.{OUTPUT_FILE_FORMAT}', index=False, sep=';')

print("Tempo total: {:.2f} segundos".format(time.time() - start_time))