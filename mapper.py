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


def traverse(schema, values):
    if isinstance(schema, (str, unicode)):
        return values[schema]
    elif isinstance(schema, dict):
        result = {}
        for key, value in schema.items():
            result[key] = traverse(value, values)
        return result
    elif isinstance(schema, list):
        result = []
        for value in schema:
            result.append(traverse(value, values))
        return result
    else:
        copy.deepcopy(schema)


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
        '--publisher-name', type=str,
        help='name of the organization that published the csv file')
    parser.add_argument(
        '--publish-date', type=str,
        help='ISO date when the csv file was published')

    options = parser.parse_args()

    with open_file_path_or_url(options.mapping_file) as mapping_file:
        content = mapping_file.read()
        result = json.loads(content)

    release_schema = result['releases'][0]
    result['releases'] = []
    result['publisher']['name'] = options.publisher_name
    result['publishingMeta']['date'] = options.publisher_name

    with open_file_path_or_url(options.csv_file) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            release = traverse(release_schema, values=row)
            result['releases'].append(release)

    print(json.dumps(result))


if __name__ == '__main__':
    main()
