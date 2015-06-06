# CoolForum database migration scripts
# Feed it JSON
import os
from os.path import join, abspath, dirname, basename
import json
import django
from django.core.mail import send_mail
from datetime import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.dev")
django.setup()

from user.models import ForumUser

here = lambda *dirs: join(abspath(dirname(__file__)), *dirs)
ADMIN_ADDRESS = 'geekattitude.forum@gmail.com'

m = "Bonjour !\n\n"\
    "L'adresse du FoRuM a changé, "\
    "vous êtes désormais les bienvenus à l'adresse suivante : htt"\
    "p://geekattitude.org/. Un mot de passe temporaire vous a été attribué. "\
    "Voici vos nouveaux identifiants :\n\n"\
    "Nom d'utilisateur : {}\nMot de passe"\
    " : {}\n\nA bientôt sur le FoRuM !\nThomas / équi"


with open('new_users.json', 'r') as f:
    credentials = json.load(f)
    for i, username in enumerate(credentials):
        try:
            user = ForumUser.objects.get(username=username)
        except ForumUser.DoesNotExist:
            continue
        if not user.is_active: continue
        print(user.email, i, len(credentials))
        send_mail(
            "L'adresse du FoRuM a changé !",
            m.format(username, credentials[username]),
            ADMIN_ADDRESS,
            [user.email],
            fail_silently=False)
