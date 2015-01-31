from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from PIL import Image
from io import BytesIO

from .models import Post


IMAGE_SIZE = 800, 450

class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit('submit', 'Enregistrer'))

    def clean_image(self, *args, **kwargs):
        # Resize image if needed
        form_img = self.cleaned_data['image']
        image = Image.open(form_img)
        image.thumbnail(IMAGE_SIZE)
        # Create a file-like object to write thumb data
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        # Create a new Django file-like object to be used as ImageField
        image = InMemoryUploadedFile(image_io, None, form_img.name,
            'image/jpeg', len(image_io.getvalue()), None)
        return image

    class Meta:
        model = Post
        fields = ['title', 'content', 'image']
