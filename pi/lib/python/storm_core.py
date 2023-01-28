from time import sleep
import sys
sys.path.insert(0,"/home/pi/lib/python")
import numpy as np
from ntcore import NetworkTableInstance
import collections

class nt_util:
    BASE_TABLE = "stormdata"
    current_index = 0
    
    def __init__(self,nt_inst,base_table=BASE_TABLE):
        self.nt_inst = nt_inst
        self.base_table = base_table
        self._structs = {}

        
    def get_base_table(self):
        return self.base_table
        
    def get_data_struct_map(self,type):
        if (type in self._structs):
            return self._structs[type]
        else:
            struct_table = self.nt_inst.getTable(self.base_table + "/structs/" + type)
            if (struct_table.containsKey("name") and struct_table.containsKey("size")):
                # populate _structs with definition from network tables
                struct_map = {}
                keys = struct_table.getStringArray("name",[]);
                values = struct_table.getNumberArray("size",[]);
                typeid = int(struct_table.getNumber("type",-1));
                struct_map["typeid"] = typeid
                struct_map["fields"] = collections.OrderedDict()
                for i in (range(len(keys))):
                    struct_map["fields"][keys[i]] = values[i]
                self._structs[type] = struct_map
                return struct_map
            else:
                return None

    def publish_data_structure(self,type,structure_definition):
        # Push a description of a data structure identified by type
        # to network tables.  everything is unsigned ints UNLESS the size is specified as negative, in which case it is signed
        # Table BASE/structs/type
        # 2 entries: names, values (stringArray,NumArray)
        # name -> # bytes.
        # This corresponds to how the data is packed into binary form
        assert isinstance(structure_definition,collections.OrderedDict)

        current_index = nt_util.current_index
        struct_map = self.get_data_struct_map(type)

        if struct_map != None:
            print("WARNING: overriding existing struct %s" % type)
            current_index = struct_map["typeid"]
            struct_map["fields"] = structure_definition
        else:
            struct_map = { "typeid": current_index, "fields": structure_definition}
            nt_util.current_index += 1
            
        table = self.nt_inst.getTable(self.base_table + "/structs/" + type)

        type_entry = table.getEntry("type")
        type_entry.setNumber(current_index)

        entry = table.getEntry("name")
        val_entry = table.getEntry("size")
        entry.setStringArray(structure_definition.keys())
        val_entry.setNumberArray(structure_definition.values())

        self._structs[type] = struct_map  # keep track of structures we know
        
        return True

    def convert_from_binary(self,type,raw_data):
        data_list = []
        struct_map = self.get_data_struct_map(type) 
        if struct_map != None:
            if (len(raw_data) == 0):
                return(data_list)
            
            data_type_index = int.from_bytes(bytes(raw_data[0:1]), byteorder='big', signed=False) #field size is 1
            num_items = int.from_bytes(raw_data[1:3],byteorder='big', signed=False);

            offset = 3;
            for item in range(num_items):
                data = {}
                for key in struct_map["fields"].keys():
                    # Determine if signed or unsiged ... negative value in structs means signed
                    data_size = struct_map["fields"][key]
                    if data_size < 0:
                        is_signed = True
                        data_size *= -1
                    else:
                        is_signed = False

                    data[key] = int.from_bytes(bytes(raw_data[offset:offset+data_size]),
                                                          byteorder='big',
                                                          signed=is_signed)
                    offset += data_size

                data_list.append(data)
        else:
            print("Id %s not a known data structure" %type)

        return data_list

    def pull_binary_data(self,name,type):
        table_name = self.base_table + "/binary_data/" + type
        table = self.nt_inst.getTable(table_name)
        entry = table.getEntry(name)
        raw_data = entry.getRaw(bytearray())
        return raw_data

    def pull_data(self,name,type):
        # serialize hash into binary data and push into network tabes
        # Table: BASE/binary/datatype
        raw_data = pull_binary_data(name,type)
        data_list = self.convert_from_binary(type,raw_data)
        return data_list

    def publish_data(self,name,type,data_list):
        # Table: BASE/binary/datatype
        raw_data = self.convert_to_binary(type,data_list)
        self.publish_binary_data(name,type,raw_data)

    def publish_binary_data(self,name,type,raw_data):
        # Table: BASE/binary/datatype
        table = self.nt_inst.getTable(self.base_table + "/binary_data/" + type)

        if raw_data != None:
            entry = table.getEntry(name)
            entry.setRaw(raw_data)
        else:
            print("Id %s not a known data structure" %type)

    def convert_to_binary(self,type,data_list):
        # serialize hash into binary data
        # Returns the raw data stream 
        struct_map = self.get_data_struct_map(type)
        raw_data = None

        if struct_map != None:
            raw_data = bytearray()

            data_type_index = struct_map["typeid"]
            raw_data += (data_type_index.to_bytes(1, byteorder='big', signed=False)) #field size is 1

            num_items = len(data_list)
            raw_data += (num_items.to_bytes(2, byteorder='big', signed=False))

            for data_hash in data_list:
                for key in struct_map["fields"].keys():
                    # Determine if signed or unsiged ... negative value in structs means signed
                    data_size = struct_map["fields"][key]
                    if data_size < 0:
                        signed = True
                        data_size *= -1
                    else:
                        signed = False

                    min_value = 0
                    max_value = 1 << (data_size * 8) - 1
                    if signed:
                        max_value = max_value/2
                        min_value = max_value * -1

                    if (key in data_hash and isinstance(data_hash[key],int)):
                        data = data_hash[key]
                        # prevent overflow conditions that crash the program by limiting the value
                        if data > max_value:
                            data = max_value
                        if data < min_value:
                            data = min_value
                    else:
                        data = 0

                    raw_data += (data.to_bytes(data_size, byteorder='big', signed=signed))
        return raw_data
