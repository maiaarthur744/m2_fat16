from root_directory import calc_root_dir_position


def rename_file(img, boot_params, old_filename, new_filename):
    if len(new_filename) > 11:
        raise ValueError("New filename must be at most 11 characters (8.3 format)")

    old_filename = old_filename.upper().ljust(11)
    new_filename = new_filename.upper().ljust(11)

    root_dir_sector, root_dir_size = calc_root_dir_position(boot_params)
    root_dir_offset = root_dir_sector * boot_params['bytes_per_block']
    img.seek(root_dir_offset)
    root_dir = img.read(root_dir_size * boot_params['bytes_per_block'])

    for i in range(0, len(root_dir), 32):
        entry = root_dir[i:i+32]
        filename = entry[:11].decode('ascii').strip()
        if filename == old_filename.strip():
            img.seek(root_dir_offset + i)
            img.write(new_filename.encode('ascii'))
            return f"File '{old_filename.strip()}' renamed to '{new_filename.strip()}'"

    return f"File '{old_filename.strip()}' not found"


def encode_time_fat16(dt):
    year = dt.year - 1980
    month = dt.month
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    second = dt.second // 2  # FAT16 armazena os segundos divididos por 2

    time = (hour << 11) | (minute << 5) | second
    date = (year << 9) | (month << 5) | day

    return date, time


def insert_file_into_image(entries, img, boot_params, root_dir_sector, root_dir_size, filename_on_host, new_filename):
    import datetime

    with open(filename_on_host, 'rb') as file:
        file_content = file.read()

    file_size = len(file_content)
    clusters_needed = (file_size + boot_params['bytes_per_cluster'] - 1) // boot_params['bytes_per_cluster']

    fat_start_sector = boot_params['reserved_blocks']
    fat_size = boot_params['blocks_per_fat'] * boot_params['bytes_per_block']
    img.seek(fat_start_sector * boot_params['bytes_per_block'])
    fat = bytearray(img.read(fat_size))

    free_clusters = []
    for i in range(2, len(fat) // 2):  # pula os dois primeiros clusters (0 e 1)
        entry = int.from_bytes(fat[i*2:i*2+2], byteorder='little')
        if entry == 0x0000:  # Cluster livre
            free_clusters.append(i)
            if len(free_clusters) == clusters_needed:
                break

    if len(free_clusters) < clusters_needed:
        raise ValueError("Não há clusters livres suficientes na imagem do disco para armazenar o arquivo.")

    # Atualiza a FAT com os clusters usados pelo novo arquivo
    for i in range(len(free_clusters) - 1):
        fat[free_clusters[i]*2:free_clusters[i]*2 +2] = (free_clusters[i+1]).to_bytes(2, byteorder='little')
    fat[free_clusters[-1]*2:free_clusters[-1]*2 +2] = (0xFFFF).to_bytes(2, byteorder='little')  # EOF

    # Escreve o conteúdo do arquivo nos clusters da imagem do disco
    data_region_start = (root_dir_sector + root_dir_size) * boot_params['bytes_per_block']
    for i, cluster in enumerate(free_clusters):
        sector = data_region_start + (cluster - 2) * boot_params['bytes_per_cluster']
        img.seek(sector)
        start = i * boot_params['bytes_per_cluster']
        end = min(start + boot_params['bytes_per_cluster'], file_size)
        img.write(file_content[start:end])

    # Atualiza a FAT na imagem do disco
    img.seek(fat_start_sector * boot_params['bytes_per_block'])
    img.write(fat)

    # Encontra uma entrada livre no diretório raiz
    root_dir_offset = root_dir_sector * boot_params['bytes_per_block']
    img.seek(root_dir_offset)
    root_dir = img.read(root_dir_size * boot_params['bytes_per_block'])

    entry_offset = None
    for i in range(0, len(root_dir), 32):
        entry = root_dir[i:i+32]
        if entry[0] == 0x00 or entry[0] == 0xE5:  # Entrada livre
            entry_offset = root_dir_offset + i
            break

    if entry_offset is None:
        raise ValueError("Não há entradas livres no diretório raiz para o novo arquivo.")

    now = datetime.datetime.now()
    specific_time = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
    creation_date, creation_time = encode_time_fat16(specific_time)
    last_mod_date, last_mod_time = encode_time_fat16(specific_time)

    # Cria a nova entrada no diretório raiz
    entry = bytearray(32)
    new_filename = new_filename.ljust(11)[:11].upper().encode('ascii')
    entry[0:11] = new_filename
    entry[11] = 0x20  # Atributos do arquivo (arquivo normal)
    entry[14:16] = creation_time.to_bytes(2, byteorder='little')
    entry[16:18] = creation_date.to_bytes(2, byteorder='little')
    entry[22:24] = last_mod_time.to_bytes(2, byteorder='little')
    entry[24:26] = last_mod_date.to_bytes(2, byteorder='little')
    entry[26:28] = free_clusters[0].to_bytes(2, byteorder='little')  # Primeiro cluster
    entry[28:32] = len(file_content).to_bytes(4, byteorder='little')  # Tamanho do arquivo

    entries.append({
        'filename': new_filename.decode('ascii').strip(),
        'attributes': {
            'is_read_only': False,
            'is_hidden': False,
            'is_system': False
        },
        'creation_time': specific_time,
        'last_mod_time': specific_time,
        'file_size': file_size,
        'starting_cluster': free_clusters[0]
    })

    # Escreve a nova entrada no diretório raiz
    img.seek(entry_offset)
    img.write(entry)
    print(f"Arquivo '{filename_on_host}' inserido como '{new_filename.decode('ascii').strip()}' na imagem do disco.")


def remove_file(img, boot_params, root_dir_sector, root_dir_size, filename, entries):
    root_dir_offset = root_dir_sector * boot_params['bytes_per_block']
    img.seek(root_dir_offset)
    root_dir = img.read(root_dir_size * boot_params['bytes_per_block'])

    print("Offset do diretório raiz: ", root_dir_offset)

    entry_index = -1
    starting_cluster = None

    for i in range(0, len(root_dir), 32):
        entry = root_dir[i:i+32]

        entry_filename = entry[:11].decode('ascii', errors='ignore').strip()
        if entry_filename.upper() == filename.upper() and entry[0] != 0x00 and entry[0] != 0xE5:
            print("Arquivo encontrado:", entry_filename)
            entry_index = i
            starting_cluster = int.from_bytes(entry[26:28], byteorder='little')
            break

    if entry_index == -1:
        print(f"Erro: Arquivo '{filename}' não encontrado.")
        return

    # Marcar a entrada do diretório como excluída
    img.seek(root_dir_offset + entry_index)
    img.write(b'\xE5' + entry[1:])

    # Ler a FAT
    fat_sector = boot_params['reserved_blocks']
    blocks_per_fat = boot_params['blocks_per_fat']
    fat_size = blocks_per_fat * boot_params['bytes_per_block']

    img.seek(fat_sector * boot_params['bytes_per_block'])
    fat = bytearray(img.read(fat_size))

    # Liberar os clusters na FAT
    cluster = starting_cluster
    while cluster < 0xFFF8:
        next_cluster = int.from_bytes(fat[cluster * 2:cluster * 2 + 2], byteorder='little')
        fat[cluster * 2:cluster * 2 + 2] = b'\x00\x00'
        if next_cluster >= 0xFFF8:
            break
        cluster = next_cluster

    # Escrever a FAT atualizada de volta na imagem
    img.seek(fat_sector * boot_params['bytes_per_block'])
    img.write(fat)

    # Encontrar e remover a entrada correspondente
    entry_to_remove = None
    for entry in entries:
        if entry['filename'] == filename:
            entry_to_remove = entry
            break

    if entry_to_remove:
        entries.remove(entry_to_remove)

    print(f"Arquivo '{filename}' removido com sucesso.\n")
