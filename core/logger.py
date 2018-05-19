_DEBUG = True;

def log(who, message, *values):
    if not values:
        if _DEBUG:
            print('%s: %s' % (who, message))
            # TODO: add to db or local file
    else:
        values_str = ', '.join(str(x) for x in values)
        if _DEBUG:
            print('%s: %s: %s' % (who, message, values_str))
            # TODO: add to db or local file
