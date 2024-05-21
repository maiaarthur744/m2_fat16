from boot_sector import print_boot_params, read_boot_sector
from file_operations import create_file
from root_directory import calc_root_dir_position, display_file_attributes, display_file_content, list_files, read_root_directory


def main():
    img_path = 'disco1.img'
    with open(img_path, 'rb+') as img:
        boot_params = read_boot_sector(img)
        root_dir_sector, root_dir_size = calc_root_dir_position(boot_params)

        entries = read_root_directory(img, boot_params, root_dir_sector, root_dir_size)

        print_boot_params(boot_params)
        list_files(entries)

        for entry in entries:
            display_file_content(img, boot_params, entry)
            #display_file_attributes(entry)
        
        #print("\n Renomeando o arquivo TESTE.TXT")
        #old_filename = "TESTE   TXT"  
        #new_filename = "LIXO.TXT" 
        #result = rename_file(img, boot_params, old_filename, new_filename)
        #print(result)
        
        #print("Criar um novo arquivo no diretório raiz.")
        #filename = input("Digite o nome do novo arquivo (8.3 format): ").strip().upper()
        #content = input("Digite o conteúdo do novo arquivo: ").encode('ascii')
        #create_file(img, boot_params, filename, content)

main()