# Minimum settings used for testing.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'factory_test.db',
    },
}

SITE_ID = 'testing'
INSTALLED_APPS = ['assemblyline', 'django.contrib.flatpages']
