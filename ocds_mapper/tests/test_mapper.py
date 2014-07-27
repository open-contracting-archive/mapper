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

def test_traverse_comprehends_number_tag():
    schema = 'number:num'
    csv_row = {'num': '2.7'}
    assert 2.7 == ocds_mapper.mapper.traverse(schema, csv_row)

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

def test_traverse_joins_multiple_fields_with_indexing_into_one_array():
    schema = {'bidder': [{
        'id': 'integer:bidder_#_id',
        'name': 'bidder_#_name'
    }]}
    csv_row = {
        'bidder_0_id': '0',
        'bidder_0_name': 'Zero',
        'bidder_1_id': '1',
        'bidder_1_name': 'One'
    }
    assert {'bidder': [
        {'id': 0, 'name': 'Zero'},
        {'id': 1, 'name': 'One'}
    ]} == ocds_mapper.mapper.traverse(schema, csv_row)

def test_traverse_splits_array_fields_and_creates_objects_based_on_subschema():
    schema = {'attachments': [{
        'uid': 'list:documents',
        'name': 'constant:Attachment'
    }]}
    csv_row = {'documents': 'foo.pdf, bar.pdf ,baz.pdf'}
    assert {'attachments': [
        {'uid': 'foo.pdf', 'name': 'Attachment'},
        {'uid': 'bar.pdf', 'name': 'Attachment'},
        {'uid': 'baz.pdf', 'name': 'Attachment'}
    ]} == ocds_mapper.mapper.traverse(schema, csv_row)

def test_traverse_raises_error_if_invalid_column_type_is_used():
    schema = 'foobarbaz:hello'
    csv_row = {}
    with pytest.raises(ValueError) as e:
        ocds_mapper.mapper.traverse(schema, csv_row)
    assert 'column' in e.value.message

def test_traverse_raises_error_indicating_wrong_header_for_invalid_keys():
    schema = 'foo'
    csv_row = {}
    with pytest.raises(KeyError) as e:
        ocds_mapper.mapper.traverse(schema, csv_row)
    assert 'invalid' in e.value.message

def test_traverse_raises_error_if_integer_conversion_failed():
    schema = 'integer:num'
    csv_row = {'num': 'foo'}
    with pytest.raises(ValueError) as e:
        ocds_mapper.mapper.traverse(schema, csv_row)
    assert 'not an integer' in e.value.message

def test_traverse_raises_error_if_float_conversion_failed():
    schema = 'number:num'
    csv_row = {'num': 'foo'}
    with pytest.raises(ValueError) as e:
        ocds_mapper.mapper.traverse(schema, csv_row)
    assert 'not a float' in e.value.message
