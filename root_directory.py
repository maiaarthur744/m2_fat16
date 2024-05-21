import struct
import datetime

def calc_root_dir_position(boot_params):
    first_root_dir_sector = boot_params['reserved_sectors'] + (boot_params['num_fats'] * boot_params['sectors_per_fat'])
    root_dir_size = (boot_params['max_root_dir_entries'] * 32) // boot_params['bytes_per_sector']
    
    return first_root_dir_sector, root_dir_size

# -------------------------------------------------------------------------------------------- #

def read_root_directory(img, boot_params, root_dir_sector, root_dir_size):
    root_dir_offset = root_dir_sector * boot_params['bytes_per_sector']
    img.seek(root_dir_offset)
    root_dir = img.read(root_dir_size * boot_params['bytes_per_sector'])
    
    print("Offset do diretório raiz: ", root_dir_offset)

    entries = []
    for i in range(0, len(root_dir), 32):
        entry = root_dir[i:i+32]

        filename = entry[:11].decode('ascii').strip()
        if filename and entry[0] != 0x00 and entry[0] != 0xE5:
            print ("ACHOU")
            print(entry)
            attributes = entry[11]
            is_read_only = bool(attributes & 0x01)
            is_hidden = bool(attributes & 0x02)
            is_system = bool(attributes & 0x04)
            creation_time = struct.unpack('<H', entry[14:16])[0]
            creation_date = struct.unpack('<H', entry[16:18])[0]
            last_mod_time = struct.unpack('<H', entry[22:24])[0]
            last_mod_date = struct.unpack('<H', entry[24:26])[0]

            creation_date_time = decode_date_time(creation_date, creation_time)
            last_mod_date_time = decode_date_time(last_mod_date, last_mod_time)
            
            entries.append({
                'filename': filename,
                'attributes': {
                    'is_read_only': is_read_only,
                    'is_hidden': is_hidden,
                    'is_system': is_system
                },
                'creation_time': creation_date_time,
                'last_mod_time': last_mod_date_time,
                'file_size': struct.unpack('<I', entry[28:32])[0],
                'starting_cluster': struct.unpack('<H', entry[26:28])[0]
            })

    return entries

# -------------------------------------------------------------------------------------------- #

def decode_date_time(date, time):
    year = ((date >> 9) & 0x7F) + 1980
    month = (date >> 5) & 0x0F
    day = date & 0x1F
    hour = (time >> 11) & 0x1F
    minute = (time >> 5) & 0x3F
    second = (time & 0x1F) * 2
    return datetime.datetime(year, month, day, hour, minute, second)

# -------------------------------------------------------------------------------------------- #

def list_files(entries):
    print("Arquivos encontrados:")
    for entry in entries:
        print(f"Filename: {entry['filename']}, Size: {entry['file_size']} bytes")
    print()

# -------------------------------------------------------------------------------------------- #

def display_file_content(img, boot_params, entry):
    cluster = entry['starting_cluster']
    content = read_file_content(img, boot_params, cluster, entry['file_size'])
    print(f"Content of {entry['filename']}:\n{content}")

# -------------------------------------------------------------------------------------------- #

def read_file_content(img, boot_params, cluster, size):
    sectors_per_cluster = boot_params['sectors_per_cluster']
    bytes_per_sector = boot_params['bytes_per_sector']
    root_dir_sector, _ = calc_root_dir_position(boot_params)
    data_region_start = root_dir_sector + (boot_params['max_root_dir_entries'] * 32) // bytes_per_sector

    content = bytearray()
    while size > 0:
        sector = data_region_start + (cluster - 2) * sectors_per_cluster
        img.seek(sector * bytes_per_sector)
        cluster_data = img.read(min(size, sectors_per_cluster * bytes_per_sector))
        content.extend(cluster_data)
        size -= len(cluster_data)
        cluster = get_next_cluster(img, boot_params, cluster)

    return content.decode('ascii', errors='replace')

# -------------------------------------------------------------------------------------------- #

def get_next_cluster(img, boot_params, cluster):
    fat_offset = boot_params['reserved_sectors'] * boot_params['bytes_per_sector'] + cluster * 2
    img.seek(fat_offset)
    return struct.unpack('<H', img.read(2))[0]

# -------------------------------------------------------------------------------------------- #

def display_file_attributes(entry):
    print('\n' '-------------------------------------------------' '\n')
    print(f"Attributes of {entry['filename']}:")
    print(f"  Read-only: {'Yes' if entry['attributes']['is_read_only'] else 'No'}")
    print(f"  Hidden: {'Yes' if entry['attributes']['is_hidden'] else 'No'}")
    print(f"  System: {'Yes' if entry['attributes']['is_system'] else 'No'}")
    print(f"  Creation time: {entry['creation_time']}")
    print(f"  Last modification time: {entry['last_mod_time']}")

# -------------------------------------------------------------------------------------------- #