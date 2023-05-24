from django import forms
from .models import Account


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Account
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password",
        ]

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            label = name.replace("_", " ").capitalize()
            field.widget.attrs.update(
                {"class": "form-control", "placeholder": f"Enter {label} !"}
            )

    def clean(self):
        cleanned_data = super(RegistrationForm, self).clean()
        password = cleanned_data.get("password")
        congirm_password = cleanned_data.get("confirm_password")

        if password != congirm_password:
            raise forms.ValidationError("Password does not match!")
