import datetime
import struct
from root_directory import calc_root_dir_position

def rename_file(img, boot_params, old_filename, new_filename):
    if len(new_filename) > 11:
        raise ValueError("New filename must be at most 11 characters (8.3 format)")

    old_filename = old_filename.upper().ljust(11)
    new_filename = new_filename.upper().ljust(11)

    root_dir_sector, root_dir_size = calc_root_dir_position(boot_params)
    root_dir_offset = root_dir_sector * boot_params['bytes_per_sector']
    img.seek(root_dir_offset)
    root_dir = img.read(root_dir_size * boot_params['bytes_per_sector'])

    # Find the file entry
    for i in range(0, len(root_dir), 32):
        entry = root_dir[i:i+32]
        filename = entry[:11].decode('ascii').strip()
        if filename == old_filename.strip():
            # Update the filename
            img.seek(root_dir_offset + i)
            img.write(new_filename.encode('ascii'))
            return f"File '{old_filename.strip()}' renamed to '{new_filename.strip()}'"
    
    return f"File '{old_filename.strip()}' not found"


# -------------------------------------------------------------------------------------------- #

def create_file(f, boot_params, filename, content):
    reserved_sectors = boot_params['reserved_sectors']
    num_fats = boot_params['num_fats']
    sectors_per_fat = boot_params['sectors_per_fat']
    bytes_per_sector = boot_params['bytes_per_sector']
    max_root_dir_entries = boot_params['max_root_dir_entries']
    root_offset = (reserved_sectors + (num_fats * sectors_per_fat)) * bytes_per_sector

    # Find an empty directory entry
    for entry in range(max_root_dir_entries):
        f.seek(root_offset + entry * 32)
        dir_entry = f.read(32)
        if dir_entry[0] == 0x00 or dir_entry[0] == 0xE5:
            break
    else:
        raise ValueError("No empty directory entries available")

    # Prepare the directory entry
    if '.' in filename:
        name_part, ext_part = filename.split('.')
        formatted_filename = name_part.ljust(8)[:8] + ext_part.ljust(3)[:3]
    else:
        formatted_filename = filename.ljust(11)[:11]

    # Current date and time for timestamps
    now = datetime.datetime.now()
    date = ((now.year - 1980) << 9) | (now.month << 5) | now.day
    time = (now.hour << 11) | (now.minute << 5) | (now.second // 2)

    dir_entry_data = struct.pack(
        '<11sBBBHHHHHL',
        formatted_filename.encode('ascii'), # Filename
        0x20,  # Attribute (0x20 = archive)
        0,  # Reserved
        0,  # Create time fine resolution
        time,  # Create time
        date,  # Create date
        date,  # Last access date
        0,  # Reserved for FAT32
        time,  # Write time
        date,  # Write date
        0,  # First cluster (will be updated later)
        len(content)  # File size
    )

    f.seek(root_offset + entry * 32)
    f.write(dir_entry_data)

    # Allocate clusters in FAT and write content
    # (Assuming only one cluster is needed for simplicity)
    data_area_offset = (reserved_sectors + (num_fats * sectors_per_fat) + ((max_root_dir_entries * 32) // bytes_per_sector)) * bytes_per_sector
    cluster_size = boot_params['sectors_per_cluster'] * bytes_per_sector
    first_data_cluster = 2  # Cluster numbering starts at 2
    fat_offset = reserved_sectors * bytes_per_sector

    # Find a free cluster in the FAT
    for cluster in range(first_data_cluster, boot_params['total_sectors'] // boot_params['sectors_per_cluster']):
        f.seek(fat_offset + cluster * 2)
        cluster_entry = struct.unpack('<H', f.read(2))[0]
        if cluster_entry == 0x0000:
            break
    else:
        raise ValueError("No free clusters available")

    # Update directory entry with the first cluster
    first_cluster = cluster
    f.seek(root_offset + entry * 32 + 26)
    f.write(struct.pack('<H', first_cluster))

    # Update FAT to mark the cluster as end-of-chain
    f.seek(fat_offset + first_cluster * 2)
    f.write(struct.pack('<H', 0xFFFF))

    # Write the content to the data area
    f.seek(data_area_offset + (first_cluster - 2) * cluster_size)
    f.write(content)

    print(f"Arquivo '{filename}' criado com sucesso.")

# -------------------------------------------------------------------------------------------- #

def remove_file(img, boot_params, root_dir_sector, root_dir_size, filename):
    root_dir_offset = root_dir_sector * boot_params['bytes_per_sector']
    img.seek(root_dir_offset)
    root_dir = img.read(root_dir_size * boot_params['bytes_per_sector'])
    
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
    fat_sector = boot_params['reserved_sectors']
    sectors_per_fat = boot_params['sectors_per_fat']
    fat_size = sectors_per_fat * boot_params['bytes_per_sector']

    img.seek(fat_sector * boot_params['bytes_per_sector'])
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
    img.seek(fat_sector * boot_params['bytes_per_sector'])
    img.write(fat)

    print(f"Arquivo '{filename}' removido com sucesso.")
