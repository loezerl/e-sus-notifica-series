## e-SUS Notifica


Este script tem como objetivo facilitar a comunicação com a API do [e-SUS Notifica](https://opendatasus.saude.gov.br/dataset/casos-nacionais/resource/30c7902e-fe02-4986-b69d-906ca4c2ec36) fazendo queries server-side para construir uma base temporal.
As informações por dia calculadas são:
- Quantidade de RT-PCR positivos por dia.
- Quantidade de RT-PCR negativos por dia.
- Quantidade de RT-PCR positivos nas faixas etárias:
    [0, 4], [5, 9], [10, 14], [15, 19]
    [20, 29], [30, 39], [40, 49], [50, 59]
    [60, 69], [70, 79], [80, 999]
- Quantidade de óbitos para RT-PCR positivos.


Para utilizar é necessário ter python 3.7 com as bibliotecas: 
`pandas numpy requests argparser`

Para executar:
```bash
python report.py -e sigla_estado -m municipio
```
Exemplo:
```bash
python report.py -e pr -m Cascavel
```
Se o município não for informado, o relatório contabilizará o estado inteiro. Para mais informações sobre os demais parâmetros:
```bash
python report.py -h
```

Caso queira extrair as informações de todos os estados, basta executar sem passar os argumentos:
```bash
python report.py
```
Para quaisquer dúvidas, sinta-se livre para me contatar via e-mail ou Github.