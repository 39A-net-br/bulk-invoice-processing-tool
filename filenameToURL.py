import pandas as pd
from urllib.parse import quote

# Nome do arquivo de entrada e saída
input_csv = "responses_full.csv"
output_csv = "output.csv"

# Função para codificar o caminho e substituir '%20' por '+'
def encode_filepath(path):
    if isinstance(path, str):  # Garante que o valor é uma string
        encoded_path = quote(path)
        return encoded_path.replace("%20", "+")
    return path  # Retorna o valor original se não for string

# Carregar o CSV
df = pd.read_csv(input_csv)

# Verificar se a coluna 'FilePath' existe
if "FilePath" in df.columns:
    # Aplicar a função de encoding à coluna 'FilePath'
    df["FilePath"] = df["FilePath"].apply(encode_filepath)
    
    # Salvar o resultado em um novo CSV
    df.to_csv(output_csv, index=False)
    print(f"Arquivo salvo com sucesso em '{output_csv}'!")
else:
    print("A coluna 'FilePath' não foi encontrada no arquivo CSV.")
