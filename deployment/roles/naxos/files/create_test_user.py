import django
django.setup()  # nopep8

from user.models import ForumUser


user = ForumUser.objects.create(username="test")
user.set_password("123456")
user.save()
