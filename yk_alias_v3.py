import argparse
import datetime
import struct

__author__ = 'yk'
__version__ = '.20160611'


RecordTypes = ["", "inodePath", "", "", "", "", "", "", "", "", "", "", "", "", "unicode_fileName", "unicode_volName",
               "", "", "filePath", "mountPoint"]
HFS_to_Epoch = 2082844800


class AliasRecord:
    type = 0
    length = 0
    data = None


class AliasData:
    class Header:
        type_user = None  # ignore
        length = 0
        version = 0
        kind_item = 0  # file or folder

    class Volume:
        date_creation = 0  # local time
        type_fs = ''

    class Item:
        inode_pfolder = 0
        inode = 0
        date_creation = 0

    records = []


def parse(raw_data):
    alias_data = AliasData()

    # header
    alias_data.header = AliasData.Header()
    alias_data.header.type_user = struct.unpack('4s', raw_data[0:4])[0]
    alias_data.header.length = struct.unpack('>H', raw_data[4:6])[0]
    alias_data.header.version = struct.unpack('>H', raw_data[6:8])[0]
    alias_data.header.kind_item = struct.unpack('>H', raw_data[8:10])[0]

    # volume details
    alias_data.volume = AliasData.Volume()
    alias_data.volume.date_creation = struct.unpack('>I', raw_data[12:16])[0]
    alias_data.volume.type_fs = struct.unpack('2s', raw_data[18:20])[0]

    # item details
    alias_data.item = AliasData.Item()
    alias_data.item.inode_pfolder = struct.unpack('>I', raw_data[24:28])[0]
    alias_data.item.inode = struct.unpack('>I', raw_data[28:32])[0]
    alias_data.item.date_creation = struct.unpack('>I', raw_data[34:38])[0]

    # records
    alias_data.records = []
    raw_data = raw_data[58:]
    while True:
        record = AliasRecord()
        record.type = struct.unpack('>h', raw_data[0:2])[0]
        record.length = struct.unpack('>H', raw_data[2:4])[0]
        record.data = struct.unpack(str(record.length) + 's', raw_data[4:4 + record.length])[0]
        alias_data.records.append(record)

        raw_data = raw_data[2 + 2 + record.length:]
        if (2 + 2 + record.length) % 2 != 0:
            raw_data = raw_data[1:]
        if record.type == -1:  # end of list
            break

    _interpret(alias_data)
    # _debug(alias_data, result)

    return result


def _interpret(alias_data):
    if alias_data.header.kind_item == 0:
        result['kind'] = "file"
    elif alias_data.header.kind_item == 1:
        result['kind'] = "folder"

    result['volCreationDate'] = datetime.datetime.utcfromtimestamp(alias_data.volume.date_creation -
                                                                   HFS_to_Epoch).strftime('%d %b %Y %H:%M:%S')
    result['inodeParent'] = str(alias_data.item.inode_pfolder)
    result['inode'] = str(alias_data.item.inode)
    result['fileSystemType'] = alias_data.volume.type_fs.decode('utf-8')
    result['fileCreationDate'] = datetime.datetime.utcfromtimestamp(alias_data.item.date_creation -
                                                                    HFS_to_Epoch).strftime('%d %b %Y %H:%M:%S')

    for record in alias_data.records:
        if record.type == 1:
            inode_components = []
            count_components = int(record.length / 4)
            for _ in range(count_components):
                inode_components.append(struct.unpack('>I', record.data[0:4])[0])
                record.data = record.data[4:]

            result[RecordTypes[1]] = ""
            for inode in reversed(inode_components):
                result[RecordTypes[1]] += str(inode) + '/'
        elif record.type == 14:
            result[RecordTypes[14]] = record.data.decode('utf-8').replace('\f', '').replace('\v', '')
        elif record.type == 15:
            result[RecordTypes[15]] = record.data.decode('utf-8').replace('\f', '').replace('\v', '')
        elif record.type == 18:
            result[RecordTypes[18]] = record.data.decode('utf-8')
        elif record.type == 19:
            result[RecordTypes[19]] = record.data.decode('utf-8')


def _debug(alias_data):
    print("{}".format("===== Header ====="))
    print("Length       : {}".format(alias_data.header.length))
    print("Version      : {}".format(alias_data.header.version))
    print("Item Kind    : {}".format(alias_data.header.kind_item) + " (0 = file, 1 = folder)")

    print("{}".format("===== Volume ====="))
    print("Date Creation: {}".format(alias_data.volume.date_creation))
    print("FS Type      : {}".format(alias_data.volume.type_fs.decode('utf-8')))
    
    print("{}".format("===== Item ====="))
    print("Pfolder Inode: {}".format(alias_data.item.inode_pfolder))
    print("Inode        : {}".format(alias_data.item.inode))
    print("Date Creation: {}".format(alias_data.item.date_creation))
    print("{}".format("================"))


result = {}

parser = argparse.ArgumentParser(description="Parse alias data")
parser.add_argument('raw', metavar='alias', type=str, nargs=1, help="specify path to file that contains raw alias data")
args = parser.parse_args()

with open(args.raw[0], 'rb') as raw_alias:
    file_content = raw_alias.read()
    parse(file_content)
for key, value in result.items():
    print("{}".format(key + ": " + value))
