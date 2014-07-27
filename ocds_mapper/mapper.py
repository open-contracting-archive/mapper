#!/usr/bin/env python
import argparse
import contextlib
import copy
import csv
import json
import urllib2
import urlparse
import uuid


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
        return csv_row[key].decode('utf-8')
    except KeyError as error:
        raise KeyError(
            'Mapping uses invalid CSV header "{}"'.format(error.message))


def decompose_schema(schema, csv_row, index=None, list_value=None):
    result = schema.split(':', 1)  # split at most once, i.e. only first colon
    if len(result) == 1:
        return get_csv_data(csv_row, schema, index)

    column_type, value = result
    if 'string' == column_type:
        return get_csv_data(csv_row, value, index)
    elif 'constant' == column_type:
        return value
    elif 'integer' == column_type:
        try:
            return int(get_csv_data(csv_row, value, index))
        except ValueError:
            raise ValueError(
                '"{}" is not an integer. Maybe mapping "{}" is invalid.'
                .format(get_csv_data(csv_row, value, index), schema))
    elif 'number' == column_type:
        try:
            return float(get_csv_data(csv_row, value, index))
        except ValueError:
            raise ValueError(
                '"{}" is not a float. Maybe mapping "{}" is invalid.'
                .format(get_csv_data(csv_row, value, index), schema))
    elif 'boolean' == column_type:
        return get_csv_data(csv_row, value, index).lower() in [
            '1', 't', 'true', 'yes']
    elif 'list' == column_type:
        if list_value is not None:
            return list_value
        return map(
            lambda it: it.strip(),
            get_csv_data(csv_row, value, index).split(','))

    raise ValueError('Invalid column type "{}:" -- valid column types are: '
                     'string, constant, integer, boolean.'.format(column_type))


def csv_row_has_key(schema, csv_row):
    try:
        decompose_schema(schema, csv_row)
    except:
        return False
    return True


def get_indexed_key(schema):
    if isinstance(schema, (str, unicode)):
        if '#' in schema:
            return schema
        else:
            return None
    elif isinstance(schema, dict):
        for key, value in schema.items():
            result = get_indexed_key(value)
            if result is not None:
                return result
    elif isinstance(schema, list):
        for value in schema:
            result = get_indexed_key(value)
            if result is not None:
                return result
    else:
        return None


def get_list_key(schema):
    if isinstance(schema, (str, unicode)):
        if schema.startswith('list:'):
            return schema
    elif isinstance(schema, dict):
        for key, value in schema.items():
            result = get_list_key(value)
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


def get_start_index(indexed_key, csv_row):
    i = 0
    if not csv_row_has_key(indexed_key.replace('#', str(i)),
                            csv_row):
        # in case indexing starts at 1, foo_0_bar would fail
        i = 1
    if not csv_row_has_key(indexed_key.replace('#', str(i)),
                            csv_row):
        raise ValueError(
            'Did not found columns for indexed key "{}", '
            'i.e. neither "{}" nor "{}" was a valid column.'
            .format(
                indexed_key,
                indexed_key.replace('#', '0'),
                indexed_key.replace('#', '1')
            )
        )
    return i


def create_list_of_indexed_objects(indexed_key, csv_row, schema, list_value):
    i = get_start_index(indexed_key, csv_row)

    result = []
    while csv_row_has_key(
            indexed_key.replace('#', str(i)), csv_row):
        for value in schema:
            result.append(traverse(value, csv_row, i, list_value))
        i += 1
    return result


def traverse_list(schema, csv_row, index, list_value):
    indexed_key = get_indexed_key(schema)
    if indexed_key is not None:
        return create_list_of_indexed_objects(
            indexed_key, csv_row, schema, list_value
        )

    result = []
    for value in schema:
        list_key = get_list_key(value)
        if list_key is not None:
            list_values = decompose_schema(list_key, csv_row, index)
            for list_value in list_values:
                result.append(traverse(value, csv_row, index, list_value))
        else:
            result.append(traverse(value, csv_row, index, list_value))
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


def process(csv_path, mapping_path, publisher_name, publish_date):
    with open_file_path_or_url(mapping_path) as mapping_file:
        content = mapping_file.read()
        result = json.loads(content)

    release_schema = result['releases'][0]
    result['releases'] = []
    result['publisher']['name'] = publisher_name
    result['publishingMeta']['date'] = publish_date

    with open_file_path_or_url(csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            release = traverse(release_schema, csv_row=row)
            if 'releaseID' not in release['releaseMeta']:
                release['releaseMeta']['releaseID'] = "{}-{}-{}".format(
                    publisher_name, publish_date, str(uuid.uuid4()))
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
    parser.add_argument(
        '--publisher-name', type=str, required=True,
        help='name of the organization that published the csv file')
    parser.add_argument(
        '--publish-date', type=str, required=True,
        help='ISO date when the csv file was published')

    options = parser.parse_args()

    result = process(
        options.csv_file, options.mapping_file,
        options.publisher_name, options.publish_date)
    print(result.encode('utf-8'))


if __name__ == '__main__':
    main()
