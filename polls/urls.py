from django.urls import path
from . import views

app_name = "polls"

urlpatterns = [
    path("",views.IndexView.as_view(),name="index"),
    path("<int:pk>/",views.DetailView.as_view(),name="detail"),
    path("<int:pk>/results/",views.ResultView.as_view(),name="results"),
    path("<int:question_id>/vote/",views.vote,name="vote"),
    path("create/", views.CreateQuestionView.as_view(), name="create_question"),
    path("<int:pk>/update/",views.UpdateQuestionView.as_view(),name="update_question"),
    path("<int:pk>/delete/",views.DeleteQuestionView.as_view(),name="delete_question"),
    path("register/",views.RegisterView.as_view(),name="register")
]