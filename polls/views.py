from django.shortcuts import render,get_object_or_404
from .forms import QuestionForm,CustomUserCreationForm,ChoiceFormSet
from .models import Question,Choice,Tag,UserProfile
from django.http import HttpResponseRedirect
from django.urls import reverse,reverse_lazy
from django.db.models import F
from django.views import generic,View
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        return Question.published.with_choices()[:5]
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context["all_tags"] = Tag.objects.all()
        context["total_questions"] = Question.published.count()
        return context

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())

class ResultView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

@login_required
def vote(request,question_id):
    question = get_object_or_404(Question,pk = question_id)
    try:
        selected_choice = question.choice_set.get(pk = request.POST["choice"])
    except (Choice.DoesNotExist,KeyError):
        context = {
            "question" : question,
            "error_message" : "You didn't select a choice."
        }
        return render(request,"polls/detail.html",context)
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        return HttpResponseRedirect(reverse("polls:results",args=(question.id,)))
    
# def create_question(request):
#     if request.method == "POST":
#         form = QuestionForm(request.POST)
#         if form.is_valid():
#             question = form.save()
#             return HttpResponseRedirect(reverse("polls:detail",args = (question.id,)))
    
#     else:
#         form = QuestionForm()

#     return render(request,"polls/create_question.html",{"form" : form})

# class CreateQuestionView(View):
#     def post(self,request):
#         form = QuestionForm(request.POST)
#         if form.is_valid():
#             question = form.save()
#             return HttpResponseRedirect(reverse("polls:detail",args=(question.id,)))
#         return render(request,"polls/create_question.html",{"form":form})
   
#     def get(self,request):
#         form = QuestionForm()
#         return render(request,"polls/create_question.html",{"form":form})
        
class CreateQuestionView(LoginRequiredMixin,CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "polls/create_question.html"

    def get_success_url(self):
        return reverse("polls:detail",args=(self.object.id,))
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["choices"] = ChoiceFormSet(self.request.POST)
        else:
            context["choices"] = ChoiceFormSet()
        return context
    def form_valid(self, form):
        context = self.get_context_data()
        choices = context["choices"]
        if choices.is_valid():
            self.object = form.save()
            choices.instance = self.object
            choices.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
        
    
class UpdateQuestionView(LoginRequiredMixin,UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "polls/update_question.html"

    def get_success_url(self):
        return reverse("polls:detail",args=(self.object.id,))
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["choices"] = ChoiceFormSet(self.request.POST,instance=self.object)
        else:
            context["choices"] = ChoiceFormSet(instance=self.object)
        return context
    def form_valid(self, form):
        context = self.get_context_data()
        choices = context["choices"]
        if choices.is_valid():
            self.object = form.save()
            choices.instance = self.object
            choices.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
        
    
class DeleteQuestionView(LoginRequiredMixin,DeleteView):
    model = Question
    template_name = "polls/delete_question.html"
    success_url = reverse_lazy("polls:index")

class RegisterView(View):
    def get(self,request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("polls:index"))
        form = CustomUserCreationForm()
        return render(request,"registration/register.html",{"form":form})
    
    def post(self,request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user=form.save()
            login(request,user)
            return HttpResponseRedirect(reverse("polls:index"))
        return render(request,"registration/register.html",{"form":form})