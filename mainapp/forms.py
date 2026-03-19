from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Worker, Category


# -------------------------
# Customer Registration Form
# -------------------------
class CustomerRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# -------------------------
# Worker Registration Form
# -------------------------
class WorkerRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Select Service Category",
        required=True
    )
    phone = forms.CharField(max_length=15, required=True)
    experience = forms.IntegerField(required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    area = forms.ChoiceField(
        choices=Worker.AREA_CHOICES,
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        # First save User
        user = super().save(commit=commit)

        # Then create Worker linked to User
        Worker.objects.create(
            user=user,
            category=self.cleaned_data['category'],
            phone=self.cleaned_data['phone'],
            experience=self.cleaned_data['experience'],
            address=self.cleaned_data['address'],
            area=self.cleaned_data['area']
        )

        return user


# -------------------------
# Worker Profile Edit Form
# -------------------------
class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['profile_image', 'bio']