mapper
======

Map csv files to open contracting data standard.

To Do:
- ~~grab the latest version of the json schema from [https://github.com/open-contracting/standard/blob/master/standard/schema/release-schema.json](https://github.com/open-contracting/standard/blob/master/standard/schema/release-schema.json)~~
- ~~start with a command line / python function that takes a csv file, the schema, and a map (define as you wish) as input and outputs ocds json~~
- ~~provide an option to autogenerate the releaseID~~
- ~~provide ability to take multiple csvs (may have different headings) e.g. two tender csvs and one award csv~~
- ~~accept urls as well as files~~
- package as lib
- allow ocds format to be extended (extend the mapping)

Next steps:
- build a django app so that users can build their map graphically (nothing super fancy, just not command line)
- may put into validator app

writing a map
=============

If you want to specify a constant value, use "constant:your constant here"

For a field to be mapped as a number, use "number:number_field" (otherwise, it
will be a string)

For a field to be mapped as an integer, use "integer:integer_field" (otherwise, it
will be a string)

Boolean type specified as "boolean:boolean_field" any of the following will
result in true being set: ['1', 't', 'true', 'yes']
