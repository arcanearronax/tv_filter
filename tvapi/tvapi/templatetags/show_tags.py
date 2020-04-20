from django import template
import logging

register = template.Library()
logger = logging.getLogger('viewlog')

@register.filter(name='match_found_processer')
def match_found_processer(data_point):
    logger.info('show_tags.match_found_processer: {}'.format(data_point))
    if data_point == True:
        return 'w3-pale-yellow ep-border match-info'
    else:
        return 'w3-pale-blue ep-border match-info'

@register.filter(name='get_id')
def get_id(table_data,name):
    logger.info('show_tags.get_id: {} - {}'.format(table_data,name))
    return table_data.get_data_point(name,'id')

@register.filter(name='get_point_value')
def get_point_value(data_points,data_point):
    logger.info('show_tags.get_point_value: {} - {}'.format(data_points, data_point))
    return data_points[data_point]

@register.filter(name='get_data_points')
def get_data_points(table_data, name):
    logger.info('show_tags.get_data_points: {} - {}'.format(table_data, name))
    return table_data.get_data_points(name)

@register.filter(name='get_row_data_points')
def get_row_data_points(table_data,name):
    logger.info('show_tags.get_row_data_points: {} - {}'.format(table_data.tmp_repr(), name))
    return table_data.get_row_data_points(name)

@register.filter(name='get_col_name')
def get_col_name(table_data, name):
    try:
        return table_data.data_points[name]['name_col_alt']
    except:
        return 'name'
