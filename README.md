# e-SUS Notifica


Este script tem como objetivo facilitar a comunicação com a API do [e-SUS Notifica](https://opendatasus.saude.gov.br/dataset/casos-nacionais/resource/30c7902e-fe02-4986-b69d-906ca4c2ec36) fazendo queries server-side para construir uma base temporal.
As informações por dia calculadas são:
- Quantidade de RT-PCR positivos por dia.
- Quantidade de RT-PCR negativos por dia.
- Quantidade de RT-PCR positivos nas faixas etárias:
    [0, 4], [5, 9], [10, 14], [15, 19]
    [20, 29], [30, 39], [40, 49], [50, 59]
    [60, 69], [70, 79], [80, 999]
- Quantidade de óbitos para RT-PCR positivos.

## Instalando python3 e dependências via Anaconda

1. Baixe e instale o miniconda3 em seu computador: https://docs.conda.io/en/latest/miniconda.html
2. Selecione a versão de acordo com o seu sistema operacional. Não é necessário baixar a versão com python 3.7!
3. Após seguir todos os passos da instalação, procure pelo terminal do anaconda em seu computador digitando "Anaconda".
4. Crie uma nova variável ambiente com python 3.7:
```bash
conda create -n py37 python=3.7 
```
5. Ative sua nova variável ambiente com python 3.7:
```bash
conda activate py37
```
_Usuários de MacOS_
```bash
source activate py37
```
6. Após ativar sua nova variável, ela deve ficar da seguinte maneira antes do caminho no bash `(py37)`.
7. Instale as dependências executando a seguinte linha de comando:
```bash
conda install pandas numpy openpyxl requests
```
8. Navegue até o diretório do repositório e siga o tutorial abaixo para extrair as informações desejadas.

*Usuários do sistema operacional MacOS Big Sur poderão enfrentar problemas durante a instalação do ambiente python.*

## Extraindo o relatório

A extração do relatório com as informações listadas anteriormente pode ser realizada das seguintes maneiras:


### Todos os Estados (Brasil)
Para extrair as informações de todos estados basta executar o script da seguinte maneira:
```bash
python report.py
```

### Região do Brasil
Caso você queira extrair as informações de uma determinada região, basta informar o nome dessa região ao parâmetro `-r`:
```bash
python report.py -r sul
```
O relatório resultante será da combinação de todos os estados presentes na região.

### Filtro por Estado único
```bash
python report.py -e sigla_estado
```
Exemplo com os dados do Paraná:
```bash
python report.py -e pr
```

### Filtro por Estados combinados
Para extrair as informações de mais de um estado, basta informar as siglas dos estados desejados separados por vígula `,`:
```bash
python report.py -e pr,rs,sc
```
O relatório resultante será da combinação de todos os estados informados no parâmetro. **Não** é possível informar estados combinados **e** município.

### Filtro por Município

Para extrair as informações para determinado município, é necessário informar o estado e município.
```bash
python report.py -e sigla_estado -m município
```
Exemplo:
```bash
python report.py -e pr -m Cascavel
```
Para municípios com nome composto, por exemplo: São Paulo e São José dos Pinhais, incluir o valor entre aspas duplas:
```bash
python report.py -e sp -m "São Paulo"
```

Para mais informações sobre os demais parâmetros:
```bash
python report.py -h
```

Para quaisquer dúvidas, sinta-se livre para me contatar via e-mail ou Github.