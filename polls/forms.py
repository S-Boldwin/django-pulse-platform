from .models import Question,Choice
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["question_text","pub_date"]
        labels = {
            "question_text" : "Question",
            "pub_date" : "Publication_Date"
        }
        widgets = {
            "question_text" : forms.TextInput(attrs={
                "placeholder" : "Enter your question here",
                "class": "form-input",
            }),
            "pub_date" : forms.DateTimeInput(attrs={
                "type" : "datetime-local",
                "class" : "form-input",
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        question_text = cleaned_data.get("question_text")
        pub_date = cleaned_data.get("pub_date")
        if question_text and pub_date:
            if "urgent" in question_text.lower() and pub_date > timezone.now():
                raise forms.ValidationError("Urgent questions must be published immediately.")
            return cleaned_data
        
    def clean_question_text(self):
        text = self.cleaned_data["question_text"]
        if len(text) <10:
            raise forms.ValidationError("Question text must be at least 10 characters long.")
        if "?" not in text:
            raise forms.ValidationError("Question text must contain a question mark.")
        
        return text
    

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text = "Required. Enter a valid email address."
    )
    class Meta:
        model = User
        fields = ["username","email","password1","password2"]

    def save(self,commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
        
        return user
    
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=('choice_text',),
    extra= 3,
    can_delete= True
)