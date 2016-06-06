import argparse
import struct

__author__ = 'yk'
__version__ = 'v.20160514'
__reference__ = 'http://michaellynn.github.io/2015/10/24/apples-bookmarkdata-exposed/'


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
    result = {}
    bm_data = BookmarkData()

    # header
    bm_data.magic = raw_data[0:4].decode('utf-8')
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
            result = interpret(bm_data.data.ToCs[-1].records[-1].type, bm_data.data.records[-1], raw_data, result)

        if bm_data.data.ToCs[-1].data.offset_next_toc == 0:
            has_next_toc = False
        else:
            index_start = bm_data.data.ToCs[-1].data.offset_next_toc

    for key, value in result.items():
        print("{}".format(key + ": " + value))
    return result


def interpret(toc_record_type, record, raw_data, result):

    if toc_record_type == 4100:  # pathComponents
        result['path'] = ''
        offsets = get_offsets(record)
        for offset in offsets:
            path_component = DataRecord()
            path_component.length = struct.unpack('<I', raw_data[offset:offset + 4])[0]
            path_component.type = struct.unpack('<I', raw_data[offset + 4:offset + 8])[0]
            path_component.data = struct.unpack(str(path_component.length) + 's',
                                                raw_data[offset + 8:offset + 8 + path_component.length])[0]
            result['path'] += '/' + path_component.data.decode('utf-8')
        # print('filePath     : {}'.format(result['path']))

    elif toc_record_type == 4101:  # fileIDs
        result['inodes'] = ''
        offsets = get_offsets(record)
        for offset in offsets:
            inodes_component = DataRecord()
            inodes_component.length = struct.unpack('<I', raw_data[offset:offset + 4])[0]
            if inodes_component.length > 0:
                inodes_component.data = struct.unpack('Q', raw_data[offset + 8:offset + 8 + inodes_component.length])[0]
                result['inodes'] += '/' + str(inodes_component.data)
            else:
                result['inodes'] += '/?'
        # print('inodePath    : {}'.format(result['inodes']))

    elif toc_record_type == 4112:  # resourceProps
        # print('resourceProps: {}'.format('?'))
        pass

    elif toc_record_type == 4160:  # creationDate
        # print('creationDate : {}'.format('?'))
        pass

    elif toc_record_type == 8192:  # volInfoDepths
        # print('volInfoDepths: {}'.format('?'))
        pass

    elif toc_record_type == 8194:  # volPath
        result['volPath'] = record.data.decode('utf-8')
        # print('volPath      : {}'.format(result['volPath']))

    elif toc_record_type == 8197:  # volURL
        result['volURL'] = record.data.decode('utf-8')
        # print('volURL       : {}'.format(result['volURL']))

    elif toc_record_type == 8208:  # volName
        result['volName'] = record.data.decode('utf-8')
        # print('volName      : {}'.format(result['volName']))

    elif toc_record_type == 8209:  # volUUID
        result['volUUID'] = record.data.decode('utf-8')
        # print('volUUID      : {}'.format(result['volUUID']))

    elif toc_record_type == 8272:  # volMountURL
        # print('volMountURL  : {}'.format('?'))
        pass

    elif toc_record_type == 49169:  # user
        result['user'] = record.data.decode('utf-8')
        # print('user         : {}'.format(result['user']))

    elif toc_record_type == 61568:  # sandboxInfo
        result['sandbox'] = record.data.decode('utf-8')
        # print('sandboxInfo  : {}'.format(result['sandbox']))

    else:
        # print('record type {} is currently unknown'.format(toc_record_type))
        pass

    return result


def get_offsets(record):
    count = record.length // 4
    if record.length % 4 > 0:
        count += 1

    offsets = []
    data = record.data
    for offset in range(count):
        offsets.append(struct.unpack('<I', data[0:4])[0])
        data = data[4:]

    return offsets


parser = argparse.ArgumentParser(description="Parse bookmark data")
parser.add_argument('raw', metavar='alias', type=str, nargs=1, help="specify path to file that contains raw bookmark "
                                                                    "data")

args = parser.parse_args()
with open(args.raw[0], 'rb') as raw_bm:
    file_content = raw_bm.read()
    parse(file_content)
