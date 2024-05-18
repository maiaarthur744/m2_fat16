class RootEntry:
    def __init__(self, size, full_name, content, entry_type, last_updated):
        self.size = size
        self.full_name = full_name
        self.content = content
        self.entry_type = entry_type
        self.last_updated = last_updated

    @staticmethod
    def decode_attributes(attributes_byte):
        print(attributes_byte)
        entry_type = ""

        if attributes_byte & 0x01:
            entry_type += "Read-only"
        if attributes_byte & 0x02:
            entry_type += "Hidden"
        if attributes_byte & 0x04:
            entry_type += "System"
        else:
            entry_type += "Normal File"
        return entry_type
