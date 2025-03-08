# Leitor de Faturas em Lote

## Configuração

Para utilizar o leitor de faturas em lote você precisa incluir um .env com a url do leitor de faturas, as credenciais e o batch size desejado.

## Como funciona?

A ferramenta vai, a partir do caminho fornecido, submeter cada uma das faturas para o leitor de faturas (seja ela pdf ou imagem) e aguardar os resultados. A sequência de ação é:

- Submete N faturas, sendo N o batch size;
- Verifica em ordem de submissão os IDs de cada fatura para obter os resultados;
- Escreve os resultados em um .csv parcial;
- Inicia o próximo batch.

Apenas quando todas faturas forem processadas a ferramenta irá unificar todos .csv parciais em um arquivo final com todos os resultados.

## Batching

O objetivo de separar a execução em batches se resume mais a segurança e um pouco a paralelização. Muitos erros possíveis são tratados e geralmente não vão causar uma falha no batch, porém, ainda pode acontecer. Batches menores garantem que apenas uma pequena parte do processamento seja perdida caso isso ocorra. Porém, batches maiores tendem a processar mais rapidamente, já que quando as faturas terminam de ser submetidas a maioria delas já estará processada e o resultado será obtido rapidamente.

## Como usar

A ferramenta é simples, o caminho padrão para as faturas é a pasta `invoices` na raiz da ferramenta. Caso use esta pasta, simplesmente rode `python run.py` para iniciar o processamento. Caso deseje usar outra pasta, altere o caminho no arquivo `run.py` e em seguida rode `python run.py`.

A execução deverá se iniciar indicando o progresso e status das faturas submetidas. Quando a execução terminar, você terá um arquivo chamado `responses_full.csv` na pasta raiz da ferramenta.