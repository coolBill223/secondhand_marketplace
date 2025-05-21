from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'price', 'is_featured']


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class ItemImageForm(forms.Form):
    images = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False
    )

    def clean_images(self):
        images = self.files.getlist('images')
        for image in images:
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError("Only image files are allowed.")
        return images
