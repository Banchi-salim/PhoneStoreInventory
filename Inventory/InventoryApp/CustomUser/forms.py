from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from inventory.InventoryApp.inventory.models import Branch


class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users with extended fields.
    """

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'address', 'branch',
                  'profile_image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True)

        # Optional fields for staff users
        if self.data.get('user_type') == 'staff':
            self.fields['branch'].required = True
        else:
            self.fields['branch'].required = False


class CustomUserChangeForm(UserChangeForm):
    """
    Form for updating users with extended fields.
    """
    password = None  # Remove the password field from the form

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'address', 'branch',
                  'profile_image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True)

        # Optional fields for staff users
        if self.data.get('user_type') == 'staff' or (self.instance and self.instance.user_type == 'staff'):
            self.fields['branch'].required = True
        else:
            self.fields['branch'].required = False


class ProfileForm(forms.ModelForm):
    """
    Form for users to update their own profile.
    """

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_image')
