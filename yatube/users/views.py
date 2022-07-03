from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ContactForm, CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:main_page')
    template_name = 'users/signup.html'


class Login(LoginView):
    form_class = AuthenticationForm
    success_url = reverse_lazy('posts:main_page')
    template_name = 'users/login.html'


def user_contact(request):
    if request.method == 'POST':
        form = ContactForm()
        if form.is_valid():
            # name = form.cleaned_data['name']
            # email = form.cleaned_data['email']
            # subject = form.cleaned_data['subject']
            # message = form.cleaned_data['body']
            # Здесь место для обработки полученных данных.
            form.save
            return redirect('/thank-you/')
    form = ContactForm()
    return render(request, 'users/contact.html', {'form': form})
