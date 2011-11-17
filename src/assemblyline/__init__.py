from functools import wraps, partial

__all__ = ['Factory', 'blueprint']


DEFAULT_BLUEPRINT_NAME = 'default'


def set_related(instance, related_fields):

    model_cls = instance.__class__

    # call the related fields and set them
    for field in related_fields:
        model_field = model_cls._meta.get_field_by_name(
            field)[0]

        if isinstance(related_fields[field], partial):
            related_fields[field] = (related_fields[field],)

        for related_partial in related_fields[field]:

            related_partial(
                related_fields={
                    model_field.field.name: instance,
                    },
                )


def create_related(instance, child_related, save=True, related_fields=None):

    related_fields = related_fields or {}
    for field_name in related_fields:
        setattr(instance, field_name, related_fields[field_name])

    # import pdb;pdb.set_trace()
    if save:
        instance.save()

        set_related(instance, child_related)

    return instance


class FactoryMetaclass(type):
    def __new__(meta, classname, bases, class_dict):
        new_methods = {}

        # Find all of the blueprints.
        for key, val in class_dict.iteritems():
            if hasattr(val, '_factories_blueprint') and callable(val):
                # Found a blueprint, create a 'build_' and 'create_' method for
                # it.
                def _make_method(save=False, related=False):
                    from django.db.models.fields import FieldDoesNotExist

                    def _build_method(self, blueprint=val, model_cls=val._factories_model, **kwargs):
                        properties = blueprint(self)
                        properties.update(kwargs)

                        # distinguish between direct field sets and related field sets
                        local_fields = []
                        related_fields = []
                        for property in properties.keys():

                            if property not in model_cls._meta.get_all_field_names():
                                if property[-4:] == '_set' and property[:-4] in model_cls._meta.get_all_field_names():
                                    properties[property[:-4]] = properties[property]
                                    property = property[:-4]

                            try:
                                if model_cls._meta.get_field_by_name(property)[2]:
                                    # this is a direct (local) field
                                    local_fields.append(property)
                                else:
                                    related_fields.append(property)
                            except FieldDoesNotExist:
                                print property
                                local_fields.append(property)

                        # Interpolate local property values into strings.
                        for property in local_fields:
                            if isinstance(properties[property], basestring):
                                properties[property] = properties[property] % properties

                        # Create the instance of the model with local fields
                        instance = model_cls(
                            **dict(
                                (field, properties[field])
                                for field in local_fields
                            )
                        )

                        # save it if requested -- do this before
                        # building related objects so we have an ID
                        if save:
                            instance.save()

                        # return the related callable if requested
                        if related:
                            return partial(create_related, instance,
                                           dict((f, properties[f]) for f in related_fields)
                                           )

                        # call the related fields and set them
                        set_related(instance,
                                    dict((f, properties[f]) for f in related_fields)
                                    )

                        return instance

                    # Set the docstring for the new method.
                    if save:
                        _build_method.__doc__ = "Create and save an instance of the '%s' model based on the '%s' blueprint." % (val._factories_model.__name__, key)
                    else:
                        _build_method.__doc__ = "Create but do not save an instance of the '%s' model based on the '%s' blueprint." % (val._factories_model.__name__, key)

                    return _build_method

                new_methods['build_' + key] = _make_method()
                new_methods['create_' + key] = _make_method(save=True)
                new_methods['related_' + key] = _make_method(related=True)

                if key == DEFAULT_BLUEPRINT_NAME:
                    # also add default methods
                    new_methods['build'] = _make_method()
                    new_methods['create'] = _make_method(save=True)
                    new_methods['related'] = _make_method(related=True)

        class_dict.update(new_methods)
        return type.__new__(meta, classname, bases, class_dict)


class Factory(object):
    """
    Baseclass for model factories.
    """
    __metaclass__ = FactoryMetaclass


def blueprint(model):
    """
    Decorator to mark a method as a factory blueprint.

    There is one required argument::

        model
            This specifies the model that corresponds with this blueprint.  It
            should be a string with the format: 'app_name.ModelName'.  This app
            will need to appear in INSTALLED_APPS in your project settings.

    Usage::

        @blueprint(model='auth.User')
        def basic_user():
            "Create a minimal User."
            return {
                'first_name': 'John',
                'last_name': 'Doe',
            }

    """
    def _decorator(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            return func(*args, **kwargs)

        from django.db.models import get_model
        from django.db.models.base import ModelBase

        # Get the model class from the ``model`` string.
        if isinstance(model, ModelBase):
            model_cls = model
        else:
            try:
                app_name, model_name = model.split('.')
            except ValueError:
                raise BadModelFormatError(model)
            model_cls = get_model(app_name, model_name)
            if not model_cls:
                raise ModelImportError(app_name, model_name)

        # Add some attributes to the wrapped method for use by
        # FactoryMetaclass.
        _wrapped_func._factories_model = model_cls
        _wrapped_func._factories_blueprint = True
        _wrapped_func.__doc__ = 'Blueprint: %s' % (_wrapped_func.__doc__)

        return _wrapped_func
    return _decorator


class ModelImportError(Exception):
    "Unable to import model from string."
    def __init__(self, app_name, model_name):
        self.app_name = app_name
        self.model_name = model_name

    def __str__(self):
        return "Could not import model '%s': Perhaps '%s' is not in your INSTALLED_APPS or there is a typo?" % (self.model_name, self.app_name)


class BadModelFormatError(Exception):
    "Model argument to blueprint decorator was malformed."
    def __init__(self, model_str):
        self.model_str = model_str

    def __str__(self):
        return "Value for model argument to blueprint decorator is malformed ('%s').  Expected format is 'app_name.ModelName'." % self.model_str
