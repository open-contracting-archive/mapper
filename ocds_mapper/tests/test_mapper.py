import json
import mock
import ocds_mapper.mapper
import pytest

def test_is_url_returns_true_for_urls():
    assert (
        ocds_mapper.mapper.is_url('http://example.com'),
        "Should be True but was False"
    )

def test_is_url_returns_false_for_file_paths():
    assert (
        not ocds_mapper.mapper.is_url('../data/canada/foo.csv'),
        "Should be False but was True"
    )

def test_process_creates_compatible_json_using_input_data_and_mapping():
    with mock.patch('uuid.uuid4', return_value='UUID'):
        result = ocds_mapper.mapper.process(
            'ocds_mapper/tests/test_data.csv',
            'ocds_mapper/tests/test_mapping.json',
            'John Doe', '2014-07-26')
    assert json.loads(result) == {
        "publisher": {"name": "John Doe"},
        "publishingMeta": {"date": "2014-07-26"},
        "releases": [
            {"releaseMeta": {
                "locale": "en_us",
                "ocid": "PW-$KIN-650-6155",
                "releaseID": "John Doe-2014-07-26-UUID"}},
            {"releaseMeta": {
                "locale": "en_us",
                "ocid": "PW-$VIC-242-6289",
                "releaseID": "John Doe-2014-07-26-UUID"}},
            {"releaseMeta": {
                "locale": "en_us",
                "ocid": "PW-$$XL-122-26346",
                "releaseID": "John Doe-2014-07-26-UUID"}}
        ]
    }

def test_traverse_uses_string_as_key():
    schema = 'language'
    csv_row = {'language': 'en_us'}
    assert 'en_us' == ocds_mapper.mapper.traverse(schema, csv_row)

def test_traverse_uses_string_tag_as_key():
    schema = 'string:language'
    csv_row = {'language': 'en_us'}
    assert 'en_us' == ocds_mapper.mapper.traverse(schema, csv_row)

def test_traverse_comprehends_integer_tag():
    schema = 'integer:num'
    csv_row = {'num': '12'}
    assert 12 == ocds_mapper.mapper.traverse(schema, csv_row)

def test_traverse_comprehends_boolean_tag():
    for falsy in ['0', 'f', 'false', 'False', 'no', 'No']:
        assert False == ocds_mapper.mapper.traverse(
            'boolean:finished', {'finished': falsy})

    for truly in ['1', 't', 'true', 'True', 'yes', 'Yes']:
        assert True == ocds_mapper.mapper.traverse(
            'boolean:finished', {'finished': truly})

def test_traverse_comprehends_constant_tag():
    schema = 'constant:en_us'
    csv_row = {}
    assert 'en_us' == ocds_mapper.mapper.traverse(schema, csv_row)

def test_traverse_raises_error_if_invalid_column_type_is_used():
    schema = 'foobarbaz:hello'
    csv_row = {}
    with pytest.raises(ValueError) as e:
        ocds_mapper.mapper.traverse(schema, csv_row)
    assert 'column' in e.value.message
