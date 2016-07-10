#!/bin/bash

# $1: database sqlite path
# $2: optional, out sql path

if [[ -z $2 ]]; then
    out=$2
else
    out='dump.sql'
fi

echo -e 'SET client_encoding = 'UTF8';\nSET standard_conforming_strings = off;\nSET check_function_bodies = false;\nSET client_min_messages = warning;\nSET escape_string_warning = off;\n--CREATE LANGUAGE plpgsql;\n\nCREATE SCHEMA "$$plant_name$$";\nSET search_path = "$$plant_name$$";\n' > $out
echo -e '.mode insert protocol\nselect * from protocol;\n.mode insert deviceType\nselect * from deviceType;\n.mode insert device\nselect * from device;\n.mode insert internalDataType\nselect * from internalDataType;\n.mode insert internalDatabaseType\nselect * from internalDatabaseType;\n.mode insert measureMethod\nselect * from measureMethod;\n.mode insert persistentConfig\nselect * from persistentConfig;\n.mode insert variableInfo\nselect * from variableInfo;\n.mode insert blockMem\nselect * from blockMem;\n.mode insert hasVariable\nselect * from hasVariable;\n.mode insert isActuator\nselect * from isActuator;\n.mode insert isAlarm\nselect * from isAlarm;\n.mode insert isCommand\nselect * from isCommand;\n.mode insert isContact\nselect * from isContact;;\n.mode insert isEnable\nselect * from isEnable;\n.mode insert isMeasure\nselect * from isMeasure;\n.mode insert isParam\nselect * from isParam;' | sqlite3 $1 >> $out