mapper
======

Map csv files to open contracting data standard.

To Do:
- ~~grab the latest version of the json schema from [https://github.com/open-contracting/standard/blob/master/standard/schema/release-schema.json](https://github.com/open-contracting/standard/blob/master/standard/schema/release-schema.json)~~
- ~~start with a command line / python function that takes a csv file, the schema, and a map (define as you wish) as input and outputs ocds json~~
- provide an option to autogenerate the releaseID
- ~~provide ability to take multiple csvs (may have different headings) e.g. two tender csvs and one award csv~~
- accept urls as well as files
- package as lib
- allow ocds format to be extended (extend the mapping)

Next steps:
- build a django app so that users can build their map graphically (nothing super fancy, just not command line)
- may put into validator app
