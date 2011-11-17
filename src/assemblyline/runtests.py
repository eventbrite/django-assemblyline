#This file mainly exists to allow python setup.py test to work.
import os
import sys

def runtests():

    # set the environment up so Django can find some settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'assemblyline.testsettings'

    # ...and now that it can find settings, import them
    from django.conf import settings
    from django.test.utils import get_runner

    test_runner = get_runner(settings)(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['assemblyline',])

    # exit with the failure information to satisfy unittest/setuptools
    sys.exit(failures)

if __name__ == '__main__':
    runtests()
