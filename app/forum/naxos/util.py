from os.path import join, abspath, dirname

# Snippet from Two Scoops of Django 1.6 to get relative directories
here = lambda *dirs: join(abspath(dirname(__file__)), *dirs)
BASE_DIR = here("..")
root = lambda *dirs: join(abspath(BASE_DIR), *dirs)
