from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Введите текст вашего поста',
            'group': 'Выберите группу',
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            error = 'Текст не может быть пустым'
            raise forms.ValidationError(error)
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Добавьте комментарий'
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            error = 'Текст не может быть пустым'
            raise forms.ValidationError(error)
        return data
