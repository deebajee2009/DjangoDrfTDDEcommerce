import factory
from django.contrib.auth import get_user_model
from faker import Faker
from apps.products.models import Category, Product, ProductImage
from apps.orders.models import Order, OrderItem
from apps.accounts.models import Profile

User = get_user_model()
fake = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_verified = True
    phone_number = factory.Faker('phone_number')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)

class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    bio = factory.Faker('text', max_nb_chars=200)
    location = factory.Faker('city')
    birth_date = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)

class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    is_active = True

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    description = factory.Faker('text')
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    category = factory.SubFactory(CategoryFactory)
    stock_quantity = factory.Faker('random_int', min=0, max=100)
    is_active = True

class ProductImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductImage

    product = factory.SubFactory(ProductFactory)
    image = factory.django.ImageField()
    alt_text = factory.Faker('sentence', nb_words=4)
    is_primary = False

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = 'pending'
    total_amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    shipping_address = factory.Faker('address')

class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=5)
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
