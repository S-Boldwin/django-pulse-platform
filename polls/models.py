from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model() 
# Create your models here.

class Tag(models.Model):
    name = models.CharField(max_length=50,unique=True)
    slug = models.SlugField(max_length=50,unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]

class PublishedQuestionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            pub_date__lte = timezone.now()
        )
    def with_choices(self):
        return self.get_queryset().prefetch_related(
            "tags",
            "choice_set"
        )

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published",default=timezone.now)
    tags = models.ManyToManyField(Tag,blank=True)

    objects = models.Manager()
    published = PublishedQuestionManager()

    def __str__(self):
        return self.question_text
    
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    
    def clean(self):
        if self.pub_date and self.pub_date > timezone.now() + datetime.timedelta(days=365):
            raise ValidationError({
                "pub_date": "Cannot schedule questions more than 1 year in advance."
            })
        if self.question_text and not self.question_text.strip().endswith("?"):
            raise ValidationError({
                "question_text" : "Questions should end with a question mark."
            })
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)
    
    class Meta:
        ordering = ["-pub_date"]
        indexes = [
             models.Index(fields=["pub_date"],name="pub_date_idx"),
        ]

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
    
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="profile",
        on_delete=models.CASCADE
    )
    bio = models.TextField(max_length=100,blank=True)
    location = models.CharField(max_length=100,blank=True)
    avatar_url = models.URLField(blank=True)
    questions_voted = models.ManyToManyField(
        Question,
        blank=True,
        related_name="voters"
    )

    def __str__(self):
        return f"Profile of {self.user.username}"
    
@receiver(post_save,sender=User)
def create_user_profile(sender,instance,created,**kwargs):
    if created:
        UserProfile.objects.create(user=instance)

    
