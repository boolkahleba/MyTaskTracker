from django import forms
from django.contrib.auth import authenticate
from .models import User, UserGroup, UserInGroup


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(min_length=6, widget=forms.PasswordInput)
    password2 = forms.CharField(min_length=6, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['full_name', 'email']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают')

        return cleaned_data

    def save(self, commit=True):
        user = User(
            full_name=self.cleaned_data['full_name'],
            email=self.cleaned_data['email'],
        )
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError('Неверный email или пароль')

            cleaned_data['user'] = user

        return cleaned_data


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = UserGroup
        fields = ['name']


class UserInGroupForm(forms.ModelForm):
    class Meta:
        model = UserInGroup
        fields = ['group', 'user']