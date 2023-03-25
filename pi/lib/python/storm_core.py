from time import sleep
import sys
sys.path.insert(0,"/home/pi/lib/python")
import numpy as np
from ntcore import NetworkTableInstance,PubSubOptions
import collections


class nt_util:
    BASE_TABLE = "stormdata"
    current_index = 0
    
    def __init__(self,nt_inst,base_table=BASE_TABLE):
        self.nt_inst = nt_inst
        self.base_table = base_table
        self._structs = {}
        self.publishers = {'struct':{},'data':{}}   # indexed by struct type, then definition and data

        
    def get_base_table(self):
        return self.base_table
        
    def get_data_struct_map(self,type):
        if (type in self._structs):
            return self._structs[type]
        else:
            table = self.nt_inst.getTable(self.base_table)
            name_sub = table.getStringArrayTopic("structs/" + type + "/names").subscribe([])
            encoding_sub = table.getIntegerArrayTopic("structs/" + type + "/encodings").subscribe([])
            type_sub = table.getIntegerTopic("structs/" + type + "/type").subscribe(-1)

            keys = name_sub.get()
            encodings = encoding_sub.get()
            typeid = type_sub.get(-1)
            if len(keys):
                struct_map = {}
                struct_map["typeid"] = typeid
                struct_map["fields"] = collections.OrderedDict()
                for i in (range(len(keys))):
                    struct_map["fields"][keys[i]] = encodings[i]
                self._structs[type] = struct_map
                return struct_map
            else:
                return None


    def publish_data_structure(self,type,structure_definition):
        """Publishes the specification of a complex data structure to network tables so that a reader on the other side can decode data
        type: string naming the data structure
        structure_definition: OrderedDict describing how the data structure is serialzed into a binary stream
            Keys are the name of each field to be sent
            Values are a 1 byte encoding defined in encode_coding_value()

        This method will associate a unique typeid integer with the data type and that will be transmitted in the binary packet              

        """
        # Push a description of a data structure identified by type
        # to network tables.  everything is unsigned ints UNLESS the encoding size is specified as negative, in which case it is signed
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
            

        table = self.nt_inst.getTable(self.base_table)

        publishers = {}

        name_topic = table.getStringArrayTopic("structs/" + type + "/names")
#        name_topic.setRetained(True)
        name_pub = name_topic.publish()        
        publishers['name'] = name_pub
        encoding_topic = table.getIntegerArrayTopic("structs/" + type + "/encodings")  # type (7:2) (1pppp p=precision, 0xxx0 = unsigned int, 0xxx1 = signed int) and # of bytes (2:0 111=8 bytes,00=1 byte)
#        encoding_topic.setRetained(True)
        value_pub = encoding_topic.publish()
        publishers['value'] = value_pub
        type_topic = table.getIntegerTopic("structs/" + type + "/type")  # The typeid
#        type_topic.setRetained(True)
        type_pub = type_topic.publish()
        publishers['type'] = type_pub

        print("Publishing data structure")
        name_pub.set(list(structure_definition.keys()))
        value_pub.set(list(structure_definition.values()))
        type_pub.set(current_index)

        if type not in self.publishers:
            self.publishers[type] = {}
        self.publishers[type]['struct'] = publishers
        # initialize dict for data
        self.publishers[type]['data'] = {}

        self._structs[type] = struct_map  # keep track of structures we know
        
        return True

    def encode_encoding_field(self,num_bytes,precision,signed=False):  
        """Generates the binary byte encoding representing how a number is encoded. If precision present then encoding is float, otherwise signed int for negative num_bytes and unsigned for positive
        [7] = sign bit
        [6:3] = precision - how many digits after the decimal point are represented
        [2:0] = number of bytes - how many bytes use to represent the unsigned value
        """
        byte = (abs(num_bytes)-1) & 0x3  # max 4 bytes
        if precision:  # floating number precision
            byte = byte | ((precision & 0x1f) << 2)
        if num_bytes < 0 or signed:
            byte = byte | 0x80

        return(byte)

    def decode_encoding_field(self,value):
        """Given a byte (int) representing number encoding, decode into number of bytes, precision, and sign
        [7] = sign bit
        [6:3] = precision - how many digits after the decimal point are represented
        [2:0] = number of bytes - how many bytes use to represent the unsigned value
        """
        if isinstance(value,bytes):
            value = int.from_bytes(value,byteorder='big',signed=False)

        value = abs(value)
        num_bytes = (value & 0x3) + 1

        precision = (value & 0x7f) >> 2
        if value & 0x80:
            signed = True
        else:
            signed = False
        return(num_bytes,precision,signed)            

    def value_from_bytes(self,bytes_value,encoding):
        """Given the one byte encoding field and a bytes object, return the int or float value"""
        (num_bytes,precision,is_signed) = self.decode_encoding_field(encoding)
        raw_value = int.from_bytes(bytes_value,
                                    byteorder='big',
                                    signed=is_signed)
    
        if precision > 0:  # floating point number
            value = raw_value/(precision ** 10)
        else:
            value = raw_value
        
        return value 

    def value_to_bytes(self,value,encoding):
        """Given a int/float value and the one byte encoding field, return a bytes object representing the value"""
        (num_bytes,precision,is_signed) = self.decode_encoding_field(encoding)
#        print(f'DEBUG: original value = {value}')
        if precision > 0:
            value = value * (10 ** precision)
#        print(f'DEBUG: mod {precision} value = {value}')

        if not isinstance(value,int):
            value = int(value)

 #       print(f'DEBUG: int value = {value}')

        min_value = 0
        max_value = 1 << (num_bytes * 8) - 1
        if is_signed:
            max_value = int(max_value/2)
            min_value = max_value * -1
        if value > max_value: value = max_value
        if value < min_value: value = min_value

#        print(f'DEBUG: capped value = {value}')
        return value.to_bytes(num_bytes, byteorder='big', signed=is_signed)

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
                    data_encoding= struct_map["fields"][key]
                    data[key] = self.value_from_bytes(raw_data[offset:offset+num_bytes],data_encoding)
                    offset += data_size

                data_list.append(data)
        else:
            print("Id %s not a known data structure" %type)

        return data_list

    def pull_binary_data(self,name,type):
        table = self.nt_inst.getTable(self.base_table)
        data_sub = table.getRawTopic(f'binary_data/{type}').subscribe()
        raw_data = data_sub.get(bytearray())
        # Fixme, save subscribe in object?

        return raw_data

    def pull_data(self,name,type):
        # serialize hash into binary data and push into network tabes
        # Table: BASE/binary/datatype
        raw_data = pull_binary_data(name,type)
        data_list = self.convert_from_binary(type,raw_data)
        return data_list

    def publish_data(self,name,type,data_list):
        """Given a name for this data, the data type, and a list of data structures, serialize the data and publish it to network tables"""
        # Table: BASE/binary/datatype
        raw_data = self.convert_to_binary(type,data_list)
        self.publish_binary_data(name,type,raw_data)

    def publish_binary_data(self,name,type,raw_data):
        """Given raw binary data, a name for this data, and the type of data, publish it to network tables"""
        if name not in self.publishers[type]['data']:

            # Table: BASE/binary/datatype
            table = self.nt_inst.getTable(self.base_table)
            data_pub = table.getRawTopic(f"binary_data/{type}/{name}").publish(type,PubSubOptions(sendAll=True))
            self.publishers[type]['data'][name] = data_pub
        else:
            data_pub = self.publishers[type]['data'][name]

        if raw_data != None:
#            print(f"DEBUG: {raw_data}")
            data_pub.set(raw_data)
        else:
            print(f"Id {type} not a known data structure")

    def convert_to_binary(self,type,data_list):
        """Serialize a list of data structures (field:value dicts) into binary data of a specific type"""
        # Returns the raw data stream 
        # data_list is list of dicts, each representing a data structure and getting serialized
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
                    data_encoding = struct_map["fields"][key]
                    value = data_hash[key]
                    if key in data_hash and (isinstance(value,int) or isinstance(value,float)):
                        data = value
                    else:
                        data = 0
                    data_bytes = self.value_to_bytes(data,data_encoding)
#                    print(f'DEBUG: {key} {data_encoding} {data} {data_bytes}')
                    raw_data += data_bytes
        return raw_data
