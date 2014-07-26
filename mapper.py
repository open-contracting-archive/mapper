import argparse
import csv
import json
import uuid
import copy


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

    with open(options.mapping_file, 'rb') as mapping_file:
        content = mapping_file.read()
        release_schema = json.loads(content)['releases'][0]

    with open(options.csv_file, 'rb') as csv_file:
        result = {
            'publisher': {
                'name': options.publisher_name
            },
            'publishingMeta': {
                'date': options.publish_date
            },
            'releases': []
        }

        reader = csv.DictReader(csv_file)
        for row in reader:
            release = traverse(release_schema, values=row)
            result['releases'].append(release)

    print(json.dumps(result))


if __name__ == '__main__':
    main()
