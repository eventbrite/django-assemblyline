from unittest import TestCase

from factories import Factory, blueprint
from factories.models import TestUser, TestModel


class UserFactory(Factory):

    @blueprint(model=TestUser)
    def default(self):

        return dict(
            username='abcdefg',
            )

    @blueprint(model=TestUser)
    def with_email(self):

        user = self.default()
        user['email'] = 'testing@example.com',

        return user


class ModelFactory(Factory):

    @blueprint(model=TestModel)
    def default(self):
        return {'required': 'Required Field'}


class FactoriesTests(TestCase):

    def testFactoryCreate(self):

        factory = UserFactory()
        user = factory.create_default()

        self.assert_(user.id)
        self.assertFalse(user.email)

        user = factory.create_default(
            email='test@example.com',
        )
        self.assertEqual(user.email, 'test@example.com')

        user = factory.create_with_email()
        self.assert_(user.id)
        self.assert_(user.email)

    def testDefaultFactory(self):
        """default blueprints have shortcut methods added."""

        factory = UserFactory()

        user = factory.create()
        self.assert_(user.id)

        user = factory.build()
        self.assertFalse(user.id)
        self.assert_(isinstance(user, TestUser))

    def testRelated(self):

        user_factory = UserFactory()
        model_factory = ModelFactory()

        user = user_factory.create(
            email='related@example.com',
            testmodel = model_factory.related(
                required='Foo',
            ),
        )

        self.assertEqual(user.email, 'related@example.com')
        self.assertEqual(user.testmodel_set.all().count(),
                         1)
        self.assertEqual(user.testmodel_set.all()[0].required,
                         'Foo')
        self.assertEqual(user.testmodel_set.all()[0].optional,
                         '')

    def testRelatedSetSyntax(self):

        user_factory = UserFactory()
        model_factory = ModelFactory()

        user = user_factory.create(
            email='related@example.com',
            testmodel_set = [
                model_factory.related(required='Foo'),
                model_factory.related(required='Bar'),
            ],
        )

        self.assertEqual(user.email, 'related@example.com')
        self.assertEqual(user.testmodel_set.all().count(),
                         2)
        self.assertEqual(user.testmodel_set.all()[0].required,
                         'Foo')
        self.assertEqual(user.testmodel_set.all()[1].required,
                         'Bar')
