


# crash1
- Caso inserir arquivo externo e depois tentar executar a opção de
"listar conteúdo" sem fechar o programa (funciona se fechar, abrir e executar)

line 109, in read_file_content
    sector = data_region_start + (cluster - 2) * sectors_per_cluster
TypeError: unsupported operand type(s) for -: 'list' and 'int'

# crash2 
- Caso tentar renomar o arquivo externo que foi inserido na imagem
<br>
m2_fat16/file_operations.py", line 20, in rename_file
    filename = entry[:11].decode('ascii').strip()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'ascii' codec can't decode byte 0xe5 in position 0: ordinal not in range(128)

# Arrumar
- Data (arquivo criado está vindo como 1980)
