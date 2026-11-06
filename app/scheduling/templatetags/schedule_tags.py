from django import template
register=template.Library()
@register.filter
def weekday_name(value):
    try: return ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][int(value)]
    except (ValueError,TypeError,IndexError): return ''
