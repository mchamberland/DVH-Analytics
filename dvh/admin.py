#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 13:43:28 2017
@author: nightowl
"""

from __future__ import print_function
from utilities import is_import_settings_defined, is_sql_connection_defined, validate_sql_connection
import os
import datetime
from roi_name_manager import DatabaseROIs, clean_name
from sql_connector import DVH_SQL
from dicom_to_sql import dicom_to_sql, rebuild_database
from bokeh.models.widgets import Select, Button, Tabs, Panel, TextInput, RadioButtonGroup, Div, MultiSelect, TableColumn, DataTable
from bokeh.layouts import layout
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, LabelSet, Range1d, Slider


query_source = ColumnDataSource(data=dict())

directories = {}
config = {}
categories = ["Institutional ROI", "Physician", "Physician ROI", "Variation"]
operators = ["Add", "Delete", "Rename"]

data = {'name': [],
        'x': [],
        'y': [],
        'x0': [],
        'y0': [],
        'x1': [],
        'y1': []}


def load_directories():
    global directories
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Get Import settings
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if is_import_settings_defined():
        script_dir = os.path.dirname(__file__)
        rel_path = "preferences/import_settings.txt"
        abs_file_path = os.path.join(script_dir, rel_path)

        with open(abs_file_path, 'r') as document:
            directories = {}
            for line in document:
                line = line.split()
                if not line:
                    continue
                try:
                    directories[line[0]] = line[1:][0]
                except:
                    directories[line[0]] = ''
    else:
        directories = {'inbox': '',
                       'imported': '',
                       'review': ''}


def load_sql_settings():
    global config
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Get SQL settings
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if is_sql_connection_defined():
        script_dir = os.path.dirname(__file__)
        rel_path = "preferences/sql_connection.cnf"
        abs_file_path = os.path.join(script_dir, rel_path)

        with open(abs_file_path, 'r') as document:
            config = {}
            for line in document:
                line = line.split()
                if not line:
                    continue
                try:
                    config[line[0]] = line[1:][0]
                except:
                    config[line[0]] = ''

        if 'user' not in config.keys():
            config['user'] = ''
            config['password'] = ''

    else:
        config = {'host': 'localhost',
                  'dbname': 'dvh',
                  'port': '5432',
                  'user': '',
                  'password': ''}


# Load Settings
load_directories()
load_sql_settings()

# Load ROI map
db = DatabaseROIs()


###############################
# Institutional roi functions
###############################
def delete_institutional_roi():
    db.delete_institutional_roi(select_institutional_roi.value)
    new_options = db.get_institutional_rois()
    select_institutional_roi.options = new_options
    select_institutional_roi.value = new_options[0]


def add_institutional_roi():
    new = clean_name(input_text.value)
    if len(new) > 50:
        new = new[0:50]
    if new and new not in db.get_institutional_rois():
        db.add_institutional_roi(new)
        select_institutional_roi.options = db.get_institutional_rois()
        select_institutional_roi.value = new
        input_text.value = ''
        update_select_unlinked_institutional_roi()


def select_institutional_roi_change(attr, old, new):
    update_input_text()


def update_institutional_roi_select():
    new_options = db.get_institutional_rois()
    select_institutional_roi.options = new_options
    select_institutional_roi.value = new_options[0]


def rename_institutional_roi():
    new = clean_name(input_text.value)
    db.set_institutional_roi(new, select_institutional_roi.value)
    update_institutional_roi_select()
    select_institutional_roi.value = new


##############################################
# Physician ROI functions
##############################################
def update_physician_roi(attr, old, new):
    select_physician_roi.options = db.get_physician_rois(new)
    try:
        select_physician_roi.value = select_physician_roi.options[0]
    except KeyError:
        pass


def add_physician_roi():
    new = clean_name(input_text.value)
    if len(new) > 50:
        new = new[0:50]
    if new and new not in db.get_physicians():
        db.add_physician_roi(select_physician.value, 'uncategorized', new)
        select_physician_roi.options = db.get_physician_rois(select_physician.value)
        select_physician_roi.value = new
        input_text.value = ''
    elif new in db.get_physicians():
        input_text.value = ''


def delete_physician_roi():
    if select_physician.value not in {'DEFAULT', ''}:
        db.delete_physician_roi(select_physician.value, select_physician_roi.value)
        select_physician_roi.options = db.get_physician_rois(select_physician.value)
        select_physician_roi.value = db.get_physician_rois(select_physician.value)[0]


def select_physician_roi_change(attr, old, new):
    update_variation()
    update_input_text()
    update_column_source_data()
    update_select_unlinked_institutional_roi()


def rename_physician_roi():
    new = clean_name(input_text.value)
    db.set_physician_roi(new, select_physician.value, select_physician_roi.value)
    update_physician_roi_select()
    select_physician_roi.value = new


##############################
# Physician functions
##############################
def update_physician_select():
    new_options = db.get_physicians()
    new_options.sort()
    select_physician.options = new_options
    select_physician.value = new_options[0]
    update_input_text()
    update_column_source_data()


def add_physician():
    new = clean_name(input_text.value).upper()
    if len(new) > 50:
        new = new[0:50]
    if new and new not in db.get_physicians():
        input_text.value = ''
        db.add_physician(new)
        select_physician.options = db.get_physicians()
        try:
            select_physician.value = new
        except KeyError:
            pass
    elif new in db.get_physicians():
        input_text.value = ''


def delete_physician():
    if select_physician.value != 'DEFAULT':
        db.delete_physician(select_physician.value)
        new_options = db.get_physicians()
        select_physician.options = new_options
        select_physician.value = new_options[0]


def select_physician_change(attr, old, new):
    update_physician_roi_select()
    update_input_text()
    update_select_unlinked_institutional_roi()
    update_uncategorized_variation_select()
    update_ignored_variations_select()


def rename_physician():
    new = clean_name(input_text.value)
    db.set_physician(new, select_physician.value)
    update_physician_select()
    select_physician.value = new


###################################
# Physician ROI Variation functions
###################################
def update_physician_roi_select():
    new_options = db.get_physician_rois(select_physician.value)
    select_physician_roi.options = new_options
    select_physician_roi.value = new_options[0]
    update_input_text()
    update_column_source_data()


def update_variation():
    select_variation.options = db.get_variations(select_physician.value,
                                                 select_physician_roi.value)
    select_variation.value = select_variation.options[0]


def add_variation():
    new = clean_name(input_text.value)
    if len(new) > 50:
        new = new[0:50]
    if new and new not in db.get_all_variations_of_physician(select_physician.value):
        db.add_variation(select_physician.value,
                         select_physician_roi.value,
                         new)
        select_variation.value = new
        input_text.value = ''
        update_variation()
        select_variation.value = new
    elif new in db.get_variations(select_physician.value,
                                  select_physician_roi.value):
        input_text.value = ''


def delete_variation():
    if select_variation.value != select_physician_roi.value:
        db.delete_variation(select_physician.value, select_physician_roi.value, select_variation.value)
        new_options = db.get_variations(select_physician.value, select_physician_roi.value)
        select_variation.options = new_options
        select_variation.value = new_options[0]


def select_variation_change(attr, old, new):
    update_input_text()


################
# Misc functions
################
def rename_variation():
    new = clean_name(input_text.value)
    db.set_variation(new, select_physician.value, select_physician_roi.value, select_variation.value)
    update_variation()
    select_variation.value = new


def update_input_text_title():
    input_text.title = operators[operator.active] + " " + categories[category.active] + ":"
    update_action_text()


def update_input_text_value():
    category_map = {0: select_institutional_roi.value,
                    1: select_physician.value,
                    2: select_physician_roi.value,
                    3: select_variation.value}
    if operator.active != 0:
        input_text.value = category_map[category.active]
    elif operator.active == 0 and category.active == 3:
        input_text.value = select_uncategorized_variation.value
    else:
        input_text.value = ''
    update_action_text()


def operator_change(attr, old, new):
    update_input_text()
    update_action_text()


def category_change(attr, old, new):
    update_input_text()
    update_action_text()


def update_input_text():
    update_input_text_title()
    update_input_text_value()


def update_action_text():
    category_map = {0: select_institutional_roi.value,
                    1: select_physician.value,
                    2: select_physician_roi.value,
                    3: select_variation.value}

    current = {0: db.get_institutional_rois(),
               1: db.get_physicians(),
               2: db.get_physician_rois(select_physician.value),
               3: db.get_variations(select_physician.value, select_physician_roi.value)}

    in_value = category_map[category.active]

    input_text_value = clean_name(input_text.value)
    if category.active == 1:
        input_text_value = input_text_value.upper()

    if input_text_value == '' or \
            (select_physician.value == 'DEFAULT' and category.active != 0) or \
            (operator.active == 1 and input_text_value not in current[category.active]) or \
            (operator.active == 2 and input_text_value in current[category.active]) or \
            (operator.active != 0 and category.active == 3 and select_variation.value == select_physician_roi.value):
        text = "<b>No Action</b>"

    else:

        text = "<b>" + input_text.title[:-1] + " </b><i>"
        if operator.active == 0:
            text += input_text_value
        else:
            text += in_value
        text += "</i>"
        output = input_text_value

        if operator.active == 0:
            if category.active == 2:
                text += " linked to Institutional ROI <i>uncategorized</i>"
            if category.active == 3:
                text += " linked to Physician ROI <i>" + select_physician_roi.value + "</i>"

        elif operator.active == 2:
            text += " to <i>" + output + "</i>"

    div_action.text = text
    action_button.label = input_text.title[:-1]


def input_text_change(attr, old, new):
    update_action_text()


def reload_db():
    global db, category, operator

    db = DatabaseROIs()

    category.active = 0
    operator.active = 0

    input_text.value = ''

    new_options = db.get_institutional_rois()
    select_institutional_roi.options = new_options
    select_institutional_roi.value = new_options[0]

    new_options = db.get_physicians()
    if len(new_options) > 1:
        new_value = new_options[1]
    else:
        new_value = new_options[0]
    select_physician.options = new_options
    select_physician.value = new_value


def save_db():
    db.write_to_file()
    save_button_roi.button_type = 'primary'
    save_button_roi.label = 'Map Saved'


def update_column_source_data():
    source.data = db.get_physician_roi_visual_coordinates(select_physician.value,
                                                          select_physician_roi.value)

function_map = {'Add Institutional ROI': add_institutional_roi,
                'Add Physician': add_physician,
                'Add Physician ROI': add_physician_roi,
                'Add Variation': add_variation,
                'Delete Institutional ROI': delete_institutional_roi,
                'Delete Physician': delete_physician,
                'Delete Physician ROI': delete_physician_roi,
                'Delete Variation': delete_variation,
                'Rename Institutional ROI': rename_institutional_roi,
                'Rename Physician': rename_physician,
                'Rename Physician ROI': rename_physician_roi,
                'Rename Variation': rename_variation}


def execute_button_click():
    function_map[input_text.title.strip(':')]()
    update_column_source_data()
    update_uncategorized_variation_select()
    update_save_button_status()


def unlinked_institutional_roi_change(attr, old, new):
    if select_physician.value != 'DEFAULT':
        db.set_linked_institutional_roi(new, select_physician.value, select_physician_roi.value)
        update_action_text()
        update_column_source_data()


def update_select_unlinked_institutional_roi():
    new_options = db.get_unused_institutional_rois(select_physician.value)
    new_value = db.get_institutional_roi(select_physician.value, select_physician_roi.value)
    if new_value not in new_options:
        new_options.append(new_value)
        new_options.sort()
    select_unlinked_institutional_roi.options = new_options
    select_unlinked_institutional_roi.value = new_value


def update_uncategorized_variation_change(attr, old, new):
    update_input_text()


def update_uncategorized_variation_select():
    global uncategorized_variations
    uncategorized_variations = get_uncategorized_variations(select_physician.value)
    new_options = uncategorized_variations.keys()
    new_options.sort()
    old_value_index = select_uncategorized_variation.options.index(select_uncategorized_variation.value)
    select_uncategorized_variation.options = new_options
    if old_value_index < len(new_options) - 1:
        select_uncategorized_variation.value = new_options[old_value_index]
    else:
        try:
            select_uncategorized_variation.value = new_options[old_value_index - 1]
        except IndexError:
            select_uncategorized_variation.value = new_options[0]
    update_input_text()


def update_ignored_variations_select():
    new_options = get_ignored_variations(select_physician.value).keys()
    new_options.sort()
    select_ignored_variation.options = new_options
    select_ignored_variation.value = new_options[0]


def get_uncategorized_variations(physician):
    global config
    if validate_sql_connection(config, verbose=False):
        physician = clean_name(physician).upper()
        condition = "physician_roi = 'uncategorized'"
        cursor_rtn = DVH_SQL().query('dvhs', 'roi_name, study_instance_uid', condition)
        new_uncategorized_variations = {}
        cnx = DVH_SQL()
        for row in cursor_rtn:
            variation = clean_name(str(row[0]))
            study_instance_uid = str(row[1])
            physician_db = cnx.query('plans', 'physician', "study_instance_uid = '" + study_instance_uid + "'")[0][0]
            if physician == physician_db and variation not in new_uncategorized_variations.keys():
                new_uncategorized_variations[variation] = {'roi_name': str(row[0]), 'study_instance_uid': str(row[1])}
        if new_uncategorized_variations:
            return new_uncategorized_variations
        else:
            return {' ': ''}
    else:
        return ['Could not connect to SQL']


def get_ignored_variations(physician):
    global config
    if validate_sql_connection(config, verbose=False):
        physician = clean_name(physician).upper()
        condition = "physician_roi = 'ignored'"
        cursor_rtn = DVH_SQL().query('dvhs', 'roi_name, study_instance_uid', condition)
        new_ignored_variations = {}
        cnx = DVH_SQL()
        for row in cursor_rtn:
            variation = clean_name(str(row[0]))
            study_instance_uid = str(row[1])
            physician_db = cnx.query('plans', 'physician', "study_instance_uid = '" + study_instance_uid + "'")[0][0]
            if physician == physician_db and variation not in new_ignored_variations.keys():
                new_ignored_variations[variation] = {'roi_name': str(row[0]), 'study_instance_uid': str(row[1])}
        if new_ignored_variations:
            return new_ignored_variations
        else:
            return {' ': ''}
    else:
        return ['Could not connect to SQL']


def delete_uncategorized_dvh():
    if delete_uncategorized_button_roi.button_type == 'warning':
        if select_uncategorized_variation.value != ' ':
            delete_uncategorized_button_roi.button_type = 'danger'
            delete_uncategorized_button_roi.label = 'Are you sure?'
            ignore_button_roi.button_type = 'success'
            ignore_button_roi.label = 'Cancel Delete DVH'
    else:
        roi_info = uncategorized_variations[select_uncategorized_variation.value]
        DVH_SQL().delete_dvh(roi_info['roi_name'], roi_info['study_instance_uid'])
        update_uncategorized_variation_select()
        delete_uncategorized_button_roi.button_type = 'warning'
        delete_uncategorized_button_roi.label = 'Delete DVH'


def delete_ignored_dvh():
    if delete_ignored_button_roi.button_type == 'warning':
        if select_ignored_variation.value != ' ':
            delete_ignored_button_roi.button_type = 'danger'
            delete_ignored_button_roi.label = 'Are you sure?'
            unignore_button_roi.button_type = 'success'
            unignore_button_roi.label = 'Cancel Delete DVH'
    else:
        roi_info = ignored_variations[select_ignored_variation.value]
        DVH_SQL().delete_dvh(roi_info['roi_name'], roi_info['study_instance_uid'])
        update_ignored_variations_select()
        delete_ignored_button_roi.button_type = 'warning'
        delete_ignored_button_roi.label = 'Delete DVH?'


def ignore_dvh():
    global config
    if ignore_button_roi.label == 'Cancel Delete DVH':
        ignore_button_roi.button_type = 'primary'
        ignore_button_roi.label = 'Ignore'
        delete_uncategorized_button_roi.button_type = 'warning'
        delete_uncategorized_button_roi.label = 'Delete DVH'
    else:
        cnx = DVH_SQL()
        if validate_sql_connection(config, verbose=False):
            condition = "physician_roi = 'uncategorized'"
            cursor_rtn = DVH_SQL().query('dvhs', 'roi_name, study_instance_uid', condition)
            for row in cursor_rtn:
                variation = str(row[0])
                study_instance_uid = str(row[1])
                if clean_name(variation) == select_uncategorized_variation.value:
                    cnx.update('dvhs', 'physician_roi', 'ignored', "roi_name = '" + variation +
                               "' and study_instance_uid = '" + study_instance_uid + "'")
        cnx.close()
        to_be_ignored = select_uncategorized_variation.value
        update_uncategorized_variation_select()
        update_ignored_variations_select()
        select_ignored_variation.value = to_be_ignored


def unignore_dvh():
    global config
    if unignore_button_roi.label == 'Cancel Delete DVH':
        unignore_button_roi.button_type = 'primary'
        unignore_button_roi.label = 'Ignore'
        delete_ignored_button_roi.button_type = 'warning'
        delete_ignored_button_roi.label = 'Delete DVH'
    else:
        cnx = DVH_SQL()
        if validate_sql_connection(config, verbose=False):
            condition = "physician_roi = 'ignored'"
            cursor_rtn = DVH_SQL().query('dvhs', 'roi_name, study_instance_uid', condition)
            for row in cursor_rtn:
                variation = str(row[0])
                study_instance_uid = str(row[1])
                if clean_name(variation) == select_ignored_variation.value:
                    cnx.update('dvhs', 'physician_roi', 'uncategorized', "roi_name = '" + variation +
                               "' and study_instance_uid = '" + study_instance_uid + "'")
        cnx.close()
        to_be_unignored = select_ignored_variation.value
        update_uncategorized_variation_select()
        update_ignored_variations_select()
        select_uncategorized_variation.value = to_be_unignored


def update_uncategorized_rois_in_db():
    cnx = DVH_SQL()

    cursor_rtn = cnx.query('dvhs', 'roi_name, study_instance_uid', "physician_roi = 'uncategorized'")
    progress = 0
    complete = len(cursor_rtn)
    initial_label = update_uncategorized_rois_button.label
    for row in cursor_rtn:
        progress += 1
        variation = str(row[0])
        study_instance_uid = str(row[1])
        physician = cnx.query('plans', 'physician', "study_instance_uid = '" + study_instance_uid + "'")[0][0]

        new_physician_roi = db.get_physician_roi(physician, variation)

        if new_physician_roi == 'uncategorized':
            if clean_name(variation) in db.get_institutional_rois():
                new_institutional_roi = clean_name(variation)
            else:
                new_institutional_roi = 'uncategorized'
        else:
            new_institutional_roi = db.get_institutional_roi(physician, new_physician_roi)

        condition_str = "roi_name = '" + variation + "' and study_instance_uid = '" + study_instance_uid + "'"
        cnx.update('dvhs', 'physician_roi', new_physician_roi, condition_str)
        cnx.update('dvhs', 'institutional_roi', new_institutional_roi, condition_str)

        percent = int(float(100) * (float(progress) / float(complete)))
        update_uncategorized_rois_button.label = "Remap progress: " + str(percent) + "%"

    update_uncategorized_rois_button.label = initial_label
    cnx.close()
    db.write_to_file()
    update_uncategorized_variation_select()
    update_ignored_variations_select()


def remap_all_rois_in_db():
    cnx = DVH_SQL()

    cursor_rtn = cnx.query('dvhs', 'roi_name, study_instance_uid')
    progress = 0
    complete = len(cursor_rtn)
    initial_label = remap_all_rois_button.label
    for row in cursor_rtn:
        progress += 1
        variation = str(row[0])
        study_instance_uid = str(row[1])
        physician = cnx.query('plans', 'physician', "study_instance_uid = '" + study_instance_uid + "'")[0][0]

        new_physician_roi = db.get_physician_roi(physician, variation)

        if new_physician_roi == 'uncategorized':
            if clean_name(variation) in db.get_institutional_rois():
                new_institutional_roi = clean_name(variation)
            else:
                new_institutional_roi = 'uncategorized'
        else:
            new_institutional_roi = db.get_institutional_roi(physician, new_physician_roi)

        condition_str = "roi_name = '" + variation + "' and study_instance_uid = '" + study_instance_uid + "'"
        cnx.update('dvhs', 'physician_roi', new_physician_roi, condition_str)
        cnx.update('dvhs', 'institutional_roi', new_institutional_roi, condition_str)

        percent = int(float(100) * (float(progress) / float(complete)))
        remap_all_rois_button.label = "Remap progress: " + str(percent) + "%"

    remap_all_rois_button.label = initial_label
    cnx.close()
    db.write_to_file()
    update_uncategorized_variation_select()
    update_ignored_variations_select()


def update_save_button_status():
    save_button_roi.button_type = 'success'
    save_button_roi.label = 'Map Save Needed'


def update_query_columns_ticker(attr, old, new):
    update_query_columns()


def update_query_columns():
    new_options = DVH_SQL().get_column_names(query_table.value.lower())
    new_options.pop(new_options.index('mrn'))
    new_options.pop(new_options.index('study_instance_uid'))
    if query_table.value.lower() == 'dvhs':
        new_options.pop(new_options.index('dvh_string'))
    options_tuples = []
    for option in new_options:
        options_tuples.append(tuple([option, option]))
    query_columns.options = options_tuples
    query_columns.value = ['']


def update_update_db_columns_ticker(attr, old, new):
    update_update_db_column()


def update_update_db_column():
    if update_db_table.value.lower() == 'dvhs':
        new_options = ['institutional_roi', 'physician_roi', 'roi_name', 'roi_type']
    elif update_db_table.value.lower() == 'plans':
        new_options = ['age', 'birth_date', 'patient_sex', 'physician', 'rx_dose', 'tx_modality', 'tx_site']
    elif update_db_table.value.lower() == 'rxs':
        new_options = ['plan_name', 'rx_dose', 'rx_percent']
    else:
        new_options = ['']

    update_db_column.options = new_options
    update_db_column.value = new_options[0]


def update_query_source():
    db_editor_layout.children.pop()
    columns = query_columns.value
    if 'mrn' not in columns:
        columns.insert(0, 'mrn')
    if 'study_instance_uid' not in columns:
        columns.insert(1, 'study_instance_uid')
    new_data = {}
    table_columns = []
    if not columns[-1]:
        columns.pop()
    for column in columns:
        new_data[column] = []
        table_columns.append(TableColumn(field=column, title=column))
    columns_str = ','.join(columns).strip()
    query_cursor = DVH_SQL().query(query_table.value, columns_str, query_condition.value)

    for row in query_cursor:
        for i in range(0, len(columns)):
            new_data[columns[i]].append(str(row[i]))

    query_source.data = new_data

    data_table_rxs_new = DataTable(source=query_source, columns=table_columns, width=table_slider.value, editable=True)
    db_editor_layout.children.append(data_table_rxs_new)


def update_db():
    DVH_SQL().update(update_db_table.value, update_db_column.value, update_db_value.value, update_db_condition.value)
    update_query_source()


def delete_from_db():
    condition = delete_from_db_column.value + " = '" + delete_from_db_value.value + "'"
    DVH_SQL().delete_rows(condition)
    update_query_source()


def import_inbox():
    import_inbox_button.button_type = 'warning'
    import_inbox_button.label = 'Importing...'
    dicom_to_sql()
    import_inbox_button.button_type = 'success'
    import_inbox_button.label = 'Import all from inbox'


def rebuild_db_button_click():
    rebuild_db_button.label = 'Rebuilding...'
    rebuild_database(directories['imported'])
    rebuild_db_button.label = 'Rebuild database'


def backup_db():
    backup_db_button.button_type = 'warning'
    backup_db_button.label = 'Backing up...'

    script_dir = os.path.dirname(__file__)
    abs_path = os.path.join(script_dir, "backups")
    if not os.path.isdir(abs_path):
        os.mkdir(abs_path)

    new_file = config['dbname'] +\
               '_' + str(datetime.datetime.now()).split('.')[0].replace(':', '-').replace(' ', '_') +\
               '.sql'
    abs_file_path = os.path.join(abs_path, new_file)

    os.system("pg_dumpall >" + abs_file_path)

    update_backup_select()

    backup_db_button.button_type = 'success'
    backup_db_button.label = 'Backup'


def restore_db():
    restore_db_button.label = 'Restoring...'
    restore_db_button.button_type = 'warning'

    DVH_SQL().drop_tables()

    script_dir = os.path.dirname(__file__)
    rel_path = os.path.join("backups", backup_select.value)
    abs_file_path = os.path.join(script_dir, rel_path)

    back_up_command = "psql " + config['dbname'] + " < " + abs_file_path
    os.system(back_up_command)

    restore_db_button.label = 'Restore'
    restore_db_button.button_type = 'primary'


def update_backup_select(*new_index):
    script_dir = os.path.dirname(__file__)
    abs_path = os.path.join(script_dir, 'backups')

    if not os.path.isdir(abs_path):
        os.mkdir(abs_path)

    backups = [f for f in os.listdir(abs_path) if os.path.isfile(os.path.join(abs_path, f))]
    if not backups:
        backups = ['']
    backups.sort(reverse=True)
    backup_select.options = backups
    if new_index:
        backup_select.value = backups[new_index[0]]
    else:
        backup_select.value = backups[0]


def delete_backup():
    old_index = backup_select.options.index(backup_select.value)

    script_dir = os.path.dirname(__file__)
    abs_path = os.path.join(script_dir, 'backups')
    abs_file = os.path.join(abs_path, backup_select.value)

    if os.path.isfile(abs_file):
        os.remove(abs_file)
        if old_index < len(backup_select.options) - 1:
            new_index = old_index
        else:
            new_index = len(backup_select.options) - 2
        update_backup_select(new_index)


######################################################
# Layout objects
######################################################

# !!!!!!!!!!!!!!!!!!!!!!!
# ROI Name Manger objects
# !!!!!!!!!!!!!!!!!!!!!!!
div_warning = Div(text="<b>WARNING:</b> Buttons in orange cannot be easily undone.", width=600)

# Selectors
options = db.get_institutional_rois()
select_institutional_roi = Select(value=options[0],
                                  options=options,
                                  width=300,
                                  title='All Institutional ROIs')

options = db.get_physicians()
if len(options) > 1:
    value = options[1]
else:
    value = options[0]
select_physician = Select(value=value,
                          options=options,
                          width=300,
                          title='Physician')

options = db.get_physician_rois(select_physician.value)
select_physician_roi = Select(value=options[0],
                              options=options,
                              width=300,
                              title='Physician ROIs')

options = db.get_variations(select_physician.value, select_physician_roi.value)
select_variation = Select(value=options[0],
                          options=options,
                          width=300,
                          title='Variations')

options = db.get_unused_institutional_rois(select_physician.value)
value = db.get_institutional_roi(select_physician.value, select_physician_roi.value)
if value not in options:
    options.append(value)
    options.sort()
select_unlinked_institutional_roi = Select(value=value,
                                           options=options,
                                           width=300,
                                           title='Linked Institutional ROI')
uncategorized_variations = get_uncategorized_variations(select_physician.value)
try:
    options = uncategorized_variations.keys()
except:
    options = ['']
options.sort()
select_uncategorized_variation = Select(value=options[0],
                                        options=options,
                                        width=300,
                                        title='Uncategorized Variations')
ignored_variations = get_ignored_variations(select_physician.value)
try:
    options = ignored_variations.keys()
except:
    options = ['']
if not options:
    options = ['']
else:
    options.sort()
select_ignored_variation = Select(value=options[0],
                                  options=options,
                                  width=300,
                                  title='Ignored Variations')

div_horizontal_bar1 = Div(text="<hr>", width=900)
div_horizontal_bar2 = Div(text="<hr>", width=900)

div_action = Div(text="<b>No Action</b>", width=600)

input_text = TextInput(value='',
                       title='Add Institutional ROI:',
                       width=300)

# RadioButtonGroups
category = RadioButtonGroup(labels=categories,
                            active=0,
                            width=400)
operator = RadioButtonGroup(labels=operators,
                            active=0,
                            width=200)

# Ticker calls
select_institutional_roi.on_change('value', select_institutional_roi_change)
select_physician.on_change('value', select_physician_change)
select_physician_roi.on_change('value', select_physician_roi_change)
select_variation.on_change('value', select_variation_change)
category.on_change('active', category_change)
operator.on_change('active', operator_change)
input_text.on_change('value', input_text_change)
select_unlinked_institutional_roi.on_change('value', unlinked_institutional_roi_change)
select_uncategorized_variation.on_change('value', update_uncategorized_variation_change)

# Button objects
action_button = Button(label='Add Institutional ROI', button_type='primary', width=200)
reload_button_roi = Button(label='Reload Map', button_type='primary', width=300)
save_button_roi = Button(label='Map Saved', button_type='primary', width=300)
ignore_button_roi = Button(label='Ignore', button_type='primary', width=150)
delete_uncategorized_button_roi = Button(label='Delete DVH', button_type='warning', width=150)
unignore_button_roi = Button(label='UnIgnore', button_type='primary', width=150)
delete_ignored_button_roi = Button(label='Delete DVH', button_type='warning', width=150)
update_uncategorized_rois_button = Button(label='Update Uncategorized ROIs in DB', button_type='warning', width=300)
remap_all_rois_button = Button(label='Remap all ROIs in DB', button_type='warning', width=300)

# Button calls
action_button.on_click(execute_button_click)
reload_button_roi.on_click(reload_db)
save_button_roi.on_click(save_db)
delete_uncategorized_button_roi.on_click(delete_uncategorized_dvh)
ignore_button_roi.on_click(ignore_dvh)
delete_ignored_button_roi.on_click(delete_ignored_dvh)
unignore_button_roi.on_click(unignore_dvh)
update_uncategorized_rois_button.on_click(update_uncategorized_rois_in_db)
remap_all_rois_button.on_click(remap_all_rois_in_db)

# Plot
p = figure(plot_width=1000, plot_height=500,
           x_range=["Institutional ROI", "Physician ROI", "Variations"],
           x_axis_location="above",
           title="(Linked by Physician and Physician ROI dropdowns)",
           tools="pan, ywheel_zoom",
           logo=None)
p.toolbar.active_scroll = "auto"
p.title.align = 'center'
p.title.text_font_style = "italic"
p.xaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.xaxis.major_label_text_font_size = "15pt"
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.yaxis.visible = False
p.outline_line_color = None
p.y_range = Range1d(-5, 5)

source = ColumnDataSource(data=data)
p.circle("x", "y", size=12, source=source, line_color="black", fill_alpha=0.8)
labels = LabelSet(x="x", y="y", text="name", y_offset=8,
                  text_font_size="15pt", text_color="#555555",
                  source=source, text_align='center')
p.add_layout(labels)
p.segment(x0='x0', y0='y0', x1='x1', y1='y1', source=source, alpha=0.5)
update_column_source_data()

roi_layout = layout([[select_institutional_roi],
                     [div_horizontal_bar1],
                     [select_physician],
                     [select_physician_roi, select_variation, select_unlinked_institutional_roi],
                     [select_uncategorized_variation, select_ignored_variation],
                     [ignore_button_roi, delete_uncategorized_button_roi, unignore_button_roi,
                      delete_ignored_button_roi],
                     [reload_button_roi, save_button_roi],
                     [update_uncategorized_rois_button, remap_all_rois_button],
                     [div_warning],
                     [div_horizontal_bar2],
                     [input_text, operator, category],
                     [div_action],
                     [action_button],
                     [p]])

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Database Editor Objects
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
import_inbox_button = Button(label='Import all from inbox', button_type='success', width=200)
import_inbox_button.on_click(import_inbox)
rebuild_db_button = Button(label='Rebuild database', button_type='warning', width=200)
rebuild_db_button.on_click(rebuild_db_button_click)

query_title = Div(text="<b>Query Database</b>", width=1000)
query_table = Select(value='DVHs', options=['DVHs', 'Plans', 'Rxs', 'Beams'], width=200, height=100, title='Table')
query_columns = MultiSelect(title="Columns (Ctrl or Shift Click enabled)", width=250, options=[tuple(['', ''])])
query_condition = TextInput(value='', title="Condition", width=300)
query_button = Button(label='Query', button_type='primary', width=100)
table_slider = Slider(start=300, end=2000, value=1000, step=10, title="Table Width")

query_table.on_change('value', update_query_columns_ticker)
query_button.on_click(update_query_source)

update_db_title = Div(text="<b>Update Database</b>", width=1000)
update_db_table = Select(value='DVHs', options=['DVHs', 'Plans', 'Rxs'], width=200, height=100, title='Table')
update_db_column = Select(value='', options=[''], width=250, title='Column')
update_db_value = TextInput(value='', title="Value", width=300)
update_db_condition = TextInput(value='', title="Condition", width=300)
update_db_button = Button(label='Update', button_type='warning', width=100)

update_db_table.on_change('value', update_update_db_columns_ticker)
update_db_button.on_click(update_db)

update_query_columns()
update_update_db_column()

data_table_rxs = DataTable(source=query_source, columns=[], width=1000)

delete_from_db_title = Div(text="<b>Delete all data with mrn or study_instance_uid</b>", width=1000)
delete_from_db_column = Select(value='mrn', options=['mrn', 'study_instance_uid'], width=200, height=100,
                               title='Patient Identifier')
delete_from_db_value = TextInput(value='', title="Value", width=300)
delete_from_db_button = Button(label='Delete', button_type='warning', width=100)
delete_from_db_button.on_click(delete_from_db)

db_editor_layout = layout([[import_inbox_button, rebuild_db_button],
                           [query_title],
                           [query_table, query_columns, query_condition, table_slider, query_button],
                           [update_db_title],
                           [update_db_table, update_db_column, update_db_condition, update_db_value, update_db_button],
                           [delete_from_db_title],
                           [delete_from_db_column, delete_from_db_value, delete_from_db_button],
                           [data_table_rxs]])

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Backup utility
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
backup_select = Select(value=options[0], options=options, title="Available Backups", width=250)
delete_backup_button = Button(label='Delete', button_type='warning', width=100)
restore_db_button = Button(label='Restore', button_type='primary', width=100)
backup_db_button = Button(label='Backup', button_type='success', width=100)
warning_div = Div(text="<b>WARNING:</b> Restore requires your OS user name to be both a"
                       " PostgreSQL super user and have ALL PRIVILEGES WITH GRANT OPTIONS.  Do NOT attempt otherwise."
                       " It's possible you have multiple PostgreSQL servers installed, so be sure your backup"
                       " file isn't empty.  Validate by typing 'psql' in a terminal/command prompt, then"
                       " <i>SELECT * FROM pg_settings WHERE name = 'port';</i> "
                       " The resulting port should match the port below"
                       " (i.e., make sure you're backing up the correct database).", width=550)
host_div = Div(text="<b>Host</b>: %s" % config['host'])
port_div = Div(text="<b>Port</b>: %s" % config['port'])
db_div = Div(text="<b>Database</b>: %s" % config['dbname'])

update_backup_select()

delete_backup_button.on_click(delete_backup)
backup_db_button.on_click(backup_db)
restore_db_button.on_click(restore_db)

backup_layout = layout([[backup_select, delete_backup_button, restore_db_button, backup_db_button],
                        [warning_div],
                        [host_div],
                        [port_div],
                        [db_div]])

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Tabs and document
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
roi_tab = Panel(child=roi_layout, title='ROI Name Manager')
db_tab = Panel(child=db_editor_layout, title='Database Editor')
backup_tab = Panel(child=backup_layout, title='Backup & Restore')

tabs = Tabs(tabs=[roi_tab, db_tab, backup_tab])

# Create the document Bokeh server will use to generate the webpage
curdoc().add_root(tabs)
curdoc().title = "DVH Analytics"


if __name__ == '__main__':
    pass