import os
from boot_sector import read_boot_sector, print_boot_params
from root_directory import (
    calc_root_dir_position,
    read_root_directory,
    list_files,
    display_file_content,
    display_file_attributes
)
from file_operations import rename_file, insert_file_into_image, remove_file

def main():

    menu = {
        '0': "# ------------------------------------ # ",
        '1': "1. Listar conteúdo do disco",
        '2': "2. Listar o conteúdo de um arquivo",
        '3': "3. Exibir atributos de um arquivo",
        '4': "4. Renomear um arquivo",
        '5': "5. Inserir/criar um novo arquivo",
        '6': "6. Apagar/remover um arquivo",
        '7': "7. Sair",
        '8': "# ------------------------------------ # "
    }

    img_path = 'disco1.img'
    with open(img_path, 'rb+') as img:
        boot_params = read_boot_sector(img)
        root_dir_sector, root_dir_size = calc_root_dir_position(boot_params)
        entries = read_root_directory(img, boot_params, root_dir_sector, root_dir_size)
        print_boot_params(boot_params)


        while True:

            for key in sorted(menu.keys()):
                print(menu[key])
            selection = input("Escolha uma opção: ").strip()
            os.system('cls' if os.name == 'nt' else 'clear')

            if selection == '1':
                list_files(entries)

            elif selection == '2':
                for entry in entries:
                        print("----------------------------------")
                        display_file_content(img, boot_params, entry)

            elif selection == '3':
                for entry in entries:
                        display_file_attributes(entry)

            elif selection == '4':
                print("\nDigite o nome do arquivo que deseja renomear:")
                print("Escreva no formato 8.3 (sem ponto) mesmo se houver espaço em branco")
                print("Ex: TESTX   TXT")
                old_filename = input("> ").strip().upper()
                print("\nDigite o novo nome para o arquivo escolhido que tenha os seguintes requisitos:")
                print("8 caracteres (nome) + 3 caracteres (extensão) sem ponto (.) Ex: testetxt")
                new_filename = input().strip().upper()
                result = rename_file(img, boot_params, old_filename, new_filename)
                print(result)
                entries = read_root_directory(img, boot_params, root_dir_sector, root_dir_size)

            elif selection == '5':
                #print("\nDigite o nome do arquivo que será criado:")
                #new_filename = input().strip().upper()
                #print("\nDigite o conteúdo do arquivo:")
                #file_content = input().strip()
                insert_file_into_image(entries, img, boot_params, root_dir_sector, root_dir_size, 'arquivo.txt', 'ARQUIVO TXT')
                entries = read_root_directory(img, boot_params, root_dir_sector, root_dir_size)
                #create_file(img, boot_params, new_filename, file_content)

            elif selection == '6':
                filename = input("Digite o nome do arquivo que deseja remover: ").strip()
                result = remove_file(img, boot_params,root_dir_sector, root_dir_size, filename, entries)

            elif selection == '7':
                break

            else:
                print("Digite uma opção entre 1 e 7")

if __name__ == "__main__":
    main()

