#!/usr/bin/env python
import argparse
import contextlib
import copy
import csv
import json
import urllib2
import urlparse
import uuid
from datetime import date


def is_url(file_path_or_url):
    return urlparse.urlparse(file_path_or_url).scheme != ''


@contextlib.contextmanager
def open_file_path_or_url(file_path_or_url):
    if is_url(file_path_or_url):
        with contextlib.closing(urllib2.urlopen(file_path_or_url)) as f:
            yield f
    else:
        with open(file_path_or_url, 'rb') as f:
            yield f


def get_csv_data(csv_row, key, index=None):
    if index is not None:
        key = key.replace('#', str(index))
    try:
        value = csv_row[key].decode('utf-8')
        if value == u'':
            value = None
    except KeyError as error:
        raise KeyError(
            'Mapping uses invalid CSV header "{}"'.format(error.message))
    return value


def decompose_schema(schema, csv_row, index=None, list_value=None):
    result = schema.split(':', 1)  # split at most once, i.e. only first colon
    if len(result) == 1:
        return get_csv_data(csv_row, schema, index)

    mapping_type, mapping_value = result

    # If we just want the constant from the mapping, just return that.
    if mapping_type == 'constant':
        return mapping_value

    # Get the value from the csv
    value = get_csv_data(csv_row, mapping_value, index)

    # If it's None, return that.
    if value is None:
        return value

    # If not, process into the correct format.
    if mapping_type == 'string':
        return str(value)

    if mapping_type == 'integer':
        try:
            return int(value)
        except ValueError:
            raise ValueError('"{}" is not an integer. Maybe mapping "{}" is invalid.'.format(value, schema))  # nopep8

    if mapping_type == 'number':
        try:
            return float(value)
        except ValueError:
            raise ValueError('"{}" is not a float. Maybe mapping "{}" is invalid.'.format(value, schema))  # nopep8

    if mapping_type == 'boolean':
        return value.lower() in ['1', 't', 'true', 'yes']

    if mapping_type == 'list':
        if list_value is not None:
            return list_value
        else:
            return [x.strip() for x in value.split(',')]

    raise ValueError(
        'Invalid column type "{}:" -- valid column types are: '
        'string, constant, integer, boolean.'.format(mapping_type)
    )


def csv_row_has_key(schema, csv_row):
    try:
        decompose_schema(schema, csv_row)
    except:
        return False
    return True


def get_index_pattern(schema):
    if isinstance(schema, (str, unicode)):
        if '#' in schema:
            return schema
        else:
            return None
    elif isinstance(schema, (dict, list)):
        if isinstance(schema, dict):
            schema = schema.values()
        for value in schema:
            result = get_index_pattern(value)
            if result is not None:
                return result
    else:
        return None


def get_list_tag(schema):
    if isinstance(schema, (str, unicode)):
        if schema.startswith('list:'):
            return schema
    elif isinstance(schema, dict):
        for key, value in schema.items():
            result = get_list_tag(value)
            if result is not None:
                return result
    else:
        return None


def traverse_str(schema, csv_row, index, list_value):
    if schema:
        return decompose_schema(schema, csv_row, index, list_value)
    else:
        return schema


def traverse_dict(schema, csv_row, index, list_value):
    result = {}
    for key, value in schema.items():
        result[key] = traverse(value, csv_row, index, list_value)
    return result


def get_start_index(index_pattern, csv_row):
    if csv_row_has_key(index_pattern.replace('#', str(0)), csv_row):
        return 0
    if csv_row_has_key(index_pattern.replace('#', str(1)), csv_row):
        return 1

    raise ValueError(
        'Did not found columns for indexed key "{}", '
        'i.e. neither "{}" nor "{}" was a valid column.'
        .format(
            index_pattern,
            index_pattern.replace('#', '0'),
            index_pattern.replace('#', '1')
        )
    )


def create_list_of_indexed_objects(index_pattern, csv_row, schema, list_value):
    i = get_start_index(index_pattern, csv_row)

    result = []
    while csv_row_has_key(index_pattern.replace('#', str(i)), csv_row):
        for value in schema:
            result.append(
                traverse(value, csv_row, i, list_value)
            )
        i += 1
    return result


def traverse_list(schema, csv_row, index, list_value):
    # this happens eg when bidder_#_name is in subschema
    index_pattern = get_index_pattern(schema)
    if index_pattern is not None:
        return create_list_of_indexed_objects(
            index_pattern, csv_row, schema, list_value
        )

    result = []
    for subschema in schema:
        list_tag = get_list_tag(subschema)
        if list_tag is not None:
            list_values = decompose_schema(list_tag, csv_row, index)
            if list_values is None:
                list_values = [None]
            for list_value in list_values:
                result.append(traverse(subschema, csv_row, index, list_value))
        else:
            result.append(traverse(subschema, csv_row, index, list_value))
    return result


def traverse(schema, csv_row, index=None, list_value=None):
    if isinstance(schema, (str, unicode)):
        return traverse_str(schema, csv_row, index, list_value)
    elif isinstance(schema, dict):
        return traverse_dict(schema, csv_row, index, list_value)
    elif isinstance(schema, list):
        return traverse_list(schema, csv_row, index, list_value)
    else:
        copy.deepcopy(schema)


def process(csv_path, mapping_path):
    with open_file_path_or_url(mapping_path) as f:
        result = json.loads(f.read())

    release_schema = result['releases'][0]
    result['releases'] = []

    with open_file_path_or_url(csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            release = traverse(release_schema, csv_row=row)
            if 'releaseID' not in release:
                release['releaseID'] = "{}-{}-{}".format(
                    result.get('publisher', {}).get('name'),
                    result.get('publishedDate', date.today().strftime("%Y%m%d")),  # nopep8
                    str(uuid.uuid4()))
            result['releases'].append(release)

    return json.dumps(result, indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description='Convert CSV files to the OpenContracting format using '
                    'a given mapping.')
    parser.add_argument('--csv-file', metavar='data.csv', type=str,
                        required=True, help='the csv file to convert')
    parser.add_argument(
        '--mapping-file', metavar='mapping.json', type=str, required=True,
        help='the mapping used to convert the csv file')

    options = parser.parse_args()

    result = process(
        options.csv_file, options.mapping_file)
    print(result.encode('utf-8'))


if __name__ == '__main__':
    main()
