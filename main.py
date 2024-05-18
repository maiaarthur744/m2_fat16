import os
from root_entry import RootEntry

iso_directory = "./iso"


def get_file(directory):
    files = os.listdir(directory)
    file = files[0]
    file_path = os.path.join(directory, file)
    # file_size = os.path.getsize(file_path)
    return file_path


def get_root_size(filePath, rootOffset):
    with open(filePath, "rb") as f:
        f.seek(rootOffset)
        root_size = 0
        while True:
            dir_entry = f.read(32)  # Read directory entry (32 bytes)
            # Check if end of directory
            if dir_entry == b'\x00' * 32 or dir_entry[0] == 0x00:
                break  # End of directory reached
            root_size += 32  # Increment root size by size of each directory entry

        # print("Size of root directory:", root_size, "bytes")
        return root_size


file_path = get_file(iso_directory)
if file_path:
    with open(file_path, "rb") as f:
        f.seek(0)
        boot_block = f.read(512)  # read all of the boot block

        bytes_per_sector = int.from_bytes(boot_block[11:13], byteorder='little')
        sectors_per_cluster = boot_block[13]
        bytes_per_cluster = bytes_per_sector * sectors_per_cluster
        # print("bytes_per_cluster: ", bytes_per_cluster)

        num_fats = int.from_bytes(boot_block[16:17], byteorder='little')
        # print("num_fats: ", num_fats)

        reserved_sectors = int.from_bytes(boot_block[14:16], byteorder='little')
        # print("reserved_sectors: ", reserved_sectors)

        bytes_per_fat = int.from_bytes(boot_block[22:24], byteorder='little')
        # print("bytes_per_fat: ", bytes_per_fat)

        root_offset = (reserved_sectors + (num_fats * bytes_per_fat)) * bytes_per_sector
        # print("root_offset: ", root_offset)

        root_size = get_root_size(file_path, root_offset)
        f.seek(root_offset)
        root_directory = f.read(root_size)
        # print("root_directory: ", root_directory)

        entry_number = root_size // 32
        files_in_root = []

        for entry in range(entry_number):
            f.seek(root_offset)
            dir_entry = f.read(32)

            filename = dir_entry[:8].decode('ascii').strip() # Extract filename (first 8 bytes) and decode from ASCII
            extension = dir_entry[8:11].decode('ascii').strip()  # Extract extension (next 3 bytes) and decode from ASCII
            full_filename = filename
            if extension:
                full_filename += '.' + extension

            size = int.from_bytes(dir_entry[28:32], byteorder='little')

            date_bytes = dir_entry[16:18]
            date_value = int.from_bytes(date_bytes, byteorder='little')
            day = date_value & 0x1F
            month = (date_value >> 5) & 0x0F
            year = ((date_value >> 9) & 0x7F) + 1980

            attributes_byte = dir_entry[11]    # Assuming attributes byte is located at offset 11
            file_type = RootEntry.decode_attributes(attributes_byte) # Decode attributes to get entry type
            files_in_root.append(RootEntry(
                size = size,  # OK
                full_name = full_filename,  # OK
                content = b"",  #
                entry_type = file_type,  # OK
                last_updated = f"{year}-{month:02d}-{day:02d}"  # OK
            ))
            root_offset += 32

        for entry in files_in_root:
            print("Full name:", entry.full_name)
            print("Size:", entry.size)
            print("File type: ", entry.entry_type)
            print("Date of the last update:", entry.last_updated)
