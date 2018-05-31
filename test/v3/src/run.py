import config
import sys
import os


def validate_app(app_name):
    pass


def check_existing_apps():
    apps_path = config.APPS_PATH
    print 'apps path:', apps_path
    apps = []
    for root, dirs, files in os.walk('.' + apps_path):
        for app_dir in dirs:
            print 'app found:', app_dir
            apps.append(app_dir)
    return apps


def main():
    app_name = None
    if len(sys.argv) > 1:
        app_name = sys.argv[1]
    apps = check_existing_apps()
    while app_name not in apps:
        if app_name is None:
            print 'No app name specified.'
        else:
            print 'Unknown app name:', app_name
        app_name = raw_input('Please specify an app to run:')
    validate_app(app_name)

if __name__ == '__main__':
    main()
