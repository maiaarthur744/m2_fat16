import struct

def read_boot_sector(img):
    img.seek(0)
    boot_sector = img.read(512)
    
    # Sector = Bloco

    bytes_per_sector = struct.unpack('<H', boot_sector[11:13])[0]    # Número de bytes por bloco (geralmente 512)  
    sectors_per_cluster = struct.unpack('<B', boot_sector[13:14])[0] # Números de blocos por partição
    reserved_sectors = struct.unpack('<H', boot_sector[14:16])[0]    # Quantidade de blocos que o boot possui (1)
    num_fats = struct.unpack('<B', boot_sector[16:17])[0]            # Número de tabelas FAT
    max_root_dir_entries = struct.unpack('<H', boot_sector[17:19])[0]# Número de entries dentro dos diretórios root
    sectors_per_fat = struct.unpack('<H', boot_sector[22:24])[0]     # Número de blocos por FAT = Tamanho da FAT
    bytes_per_cluster = bytes_per_sector * sectors_per_cluster


    return {
        'bytes_per_sector': bytes_per_sector,
        'sectors_per_cluster': sectors_per_cluster,
        'reserved_sectors': reserved_sectors,
        'num_fats': num_fats,
        'max_root_dir_entries': max_root_dir_entries,
        'sectors_per_fat': sectors_per_fat,
        'bytes_per_cluster': bytes_per_cluster
    }

def print_boot_params(boot_params):
    print("Boot Sector Parameters:")
    for key, value in boot_params.items():
        print(f"  {key.replace('_', ' ').capitalize()}: {value}")
    print()
