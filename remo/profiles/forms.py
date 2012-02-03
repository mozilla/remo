from django import forms

class InviteUserForm(forms.Form):
    email = forms.EmailField(label='Email')
