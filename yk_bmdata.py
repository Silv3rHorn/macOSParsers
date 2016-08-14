import argparse
import datetime
import pprint
import struct

__author__ = 'yk'
__version__ = 'v.20160810'
__reference1__ = "http://michaellynn.github.io/2015/10/24/apples-bookmarkdata-exposed/"
__reference2__ = "Simon Key - Mac OS X - Delving a Little Deeper"

RecordTypes = {
    4100: 'filePath',  # pathComponents
    4101: 'fileInodePath',  # fileIDs
    4112: 'resourceProps',
    4160: 'fileCreationDate',  # creationDate
    8192: 'volInfoDepths',
    8194: 'volPath',
    8197: 'volURL',
    8208: 'volName',
    8209: 'volUUID',
    8210: 'volSize',  # volCapacity
    8211: 'volCreationDate',
    8224: 'volProps',
    8240: 'volWasBoot',
    8272: 'volMountURL',
    49153: 'volDepthCountHome',  # Vol Home Dir Relative Path Component Count
    49169: 'username',
    49170: 'userUID',
    53264: 'creationOptions',
    61463: 'displayName',
    61473: 'iconRef',  # Effective Flattened Icon Ref
    61488: 'bookmarkCreationDate',  # Bookmark Creation Time
    61568: 'sandboxInfo'  # Sandbox RW Extension
}
Cocoa_to_Epoch = 978307200


class ToCRecord:
    type = 0
    flags = 0
    offset_data_record = 0


class ToC:
    class Header:
        length = 0
        type = 0
        flags = 0

    class Data:
        level = 0
        offset_next_toc = 0
        record_count = 0

    records = []  # each element of type ToCRecord


class DataRecord:
    length = 0
    type = 0
    data = None


class BookmarkData:
    magic = ""
    length = 0
    version = 0
    offset_data = 0

    class Data:
        offset_firstToC = 0
        ToCs = []  # each element of type ToC
        records = []  # each element of type DataRecord


def parse(raw_data):
    del result[:]
    bm_data = BookmarkData()

    # header
    bm_data.magic = raw_data[0:4]
    bm_data.length = struct.unpack('<I', raw_data[4:8])[0]
    bm_data.version = struct.unpack('>I', raw_data[8:12])[0]
    bm_data.offset_data = struct.unpack('<I', raw_data[12:16])[0]

    # data
    bm_data.data = BookmarkData.Data()
    bm_data.data.ToCs = []
    bm_data.data.records = []

    index_start = bm_data.offset_data
    bm_data.data.offset_firstToC = struct.unpack('<I', raw_data[index_start:index_start + 4])[0]
    raw_data = raw_data[index_start:]

    index_start = bm_data.data.offset_firstToC
    has_next_toc = True
    while has_next_toc:
        bm_data.data.ToCs.append(ToC())
        bm_data.data.ToCs[-1].records = []
        bm_data.data.ToCs[-1].header = ToC.Header()
        bm_data.data.ToCs[-1].header.length = struct.unpack('<I', raw_data[index_start:index_start + 4])[0]
        bm_data.data.ToCs[-1].header.type = struct.unpack('<h', raw_data[index_start + 4:index_start + 6])[0]
        bm_data.data.ToCs[-1].header.flags = struct.unpack('>H', raw_data[index_start + 6:index_start + 8])[0]

        data = struct.unpack('III', raw_data[index_start + 8:index_start + 20])
        bm_data.data.ToCs[-1].data = ToC.Data()
        bm_data.data.ToCs[-1].data.level = data[0]
        bm_data.data.ToCs[-1].data.offset_next_toc = data[1]
        bm_data.data.ToCs[-1].data.record_count = data[2]

        index_start += 20
        toc = {}
        for _ in range(bm_data.data.ToCs[-1].data.record_count):
            bm_data.data.ToCs[-1].records.append(ToCRecord())
            raw_record = struct.unpack('HHI', raw_data[index_start:index_start + 8])
            bm_data.data.ToCs[-1].records[-1].type = raw_record[0]
            bm_data.data.ToCs[-1].records[-1].flags = raw_record[1]
            bm_data.data.ToCs[-1].records[-1].offset_data_record = raw_record[2]
            index_start += 12

            bm_data.data.records.append(DataRecord())
            bm_data.data.records[-1].length = struct.unpack('<I', raw_data[raw_record[2]:raw_record[2] + 4])[0]
            bm_data.data.records[-1].type = struct.unpack('<I', raw_data[raw_record[2] + 4:raw_record[2] + 8])[0]
            bm_data.data.records[-1].data = struct.unpack(str(bm_data.data.records[-1].length) + 's',
                                                          raw_data[raw_record[2] + 8:raw_record[2] + 8 + bm_data.data.
                                                          records[-1].length])[0]
            __parse_record(toc, bm_data.data, raw_data)

        if "volSize" in toc:  # make volume size human-readable
            vol_size = float(toc["volSize"])
            for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB']:
                if abs(vol_size) < 1024.0:
                    toc["volSize"] = "%3.2f%s" % (vol_size, unit)
                    break
                vol_size /= 1024.0

        result.append(toc)
        if bm_data.data.ToCs[-1].data.offset_next_toc == 0:
            has_next_toc = False
        else:
            index_start = bm_data.data.ToCs[-1].data.offset_next_toc

    return result


def __parse_record(toc, data, raw_data):
    toc_record_type = data.ToCs[-1].records[-1].type
    record = data.records[-1]
    
    parsed_record = __parse_data_type(record, raw_data)
    if parsed_record is None:
        return

    if toc_record_type in RecordTypes:
        toc[RecordTypes[toc_record_type]] = parsed_record


def __parse_data_type(record, raw_data):
    if record.type == 257:  # string
        return record.data

    elif record.type == 513:  # binary
        return None

    elif record.type == 771:  # unsigned-int (4-byte)
        return struct.unpack('<I', record.data)[0]

    elif record.type == 772:  # unsigned-int (8-byte)
        return struct.unpack('<Q', record.data)[0]

    elif record.type == 774:  # double (Date, Little-Endian)
        raw_date = struct.unpack('<d', record.data)[0]
        return datetime.datetime.utcfromtimestamp(raw_date + Cocoa_to_Epoch).strftime('%d %b %Y %H:%M:%S.%f')

    elif record.type == 1024:  # double (Date, Big-Endian)
        raw_date = struct.unpack('>d', record.data)[0]
        return datetime.datetime.utcfromtimestamp(raw_date + Cocoa_to_Epoch).strftime('%d %b %Y %H:%M:%S.%f')

    elif record.type == 1281:  # boolean true
        return "True"

    elif record.type == 1537:  # pointer array
        count = record.length // 4
        if record.length % 4 > 0:
            count += 1

        offsets = []
        for offset in range(count):
            offsets.append(struct.unpack('<I', record.data[0:4])[0])
            record.data = record.data[4:]

        components = ""
        for offset in offsets:
            component = DataRecord()
            component.length = struct.unpack('<I', raw_data[offset:offset + 4])[0]
            component.type = struct.unpack('<I', raw_data[offset + 4:offset + 8])[0]
            component.data = struct.unpack(str(component.length) + 's',
                                           raw_data[offset + 8:offset + 8 + component.length])[0]
            components += '/' + str(__parse_data_type(component, raw_data))

        return components

    elif record.type == 2305:  # CFURL
        return record.data

    else:
        return None


result = []

parser = argparse.ArgumentParser(description="Parse bookmark data")
parser.add_argument('raw', metavar='alias', type=str, nargs=1, help="specify path to file that contains raw bookmark "
                                                                    "data")
args = parser.parse_args()

with open(args.raw[0], 'rb') as raw_bm:
    file_content = raw_bm.read()
    parse(file_content)
for table in result:
    print('=' * 10 + " TOC " + str(result.index(table)) + ' ' + '=' * 10)
    pprint.pprint(table)
