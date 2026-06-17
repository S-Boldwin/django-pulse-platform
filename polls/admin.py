from django.contrib import admin
from django.utils import timezone
from .models import Question, Choice, Tag, UserProfile

# Choice layout configuration nested within individual Question forms
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2  
    fields = ["choice_text", "votes"]
    readonly_fields = ["votes"] 


# Custom filter box on the right sidebar to find questions with or without choices
class HasChoicesFilter(admin.SimpleListFilter):
    title = "has choices"
    parameter_name = "has_choices"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Has choices"),
            ("no", "No choices"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(choice_set__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(choice_set__isnull=True)
        return queryset

# Main dashboard setup for managing poll questions
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = [
        "question_text",
        "pub_date",
        "was_published_recently",
        "choice_count", 
    ]
    list_filter = ["pub_date", "tags", HasChoicesFilter]  
    search_fields = ["question_text"]
    date_hierarchy = "pub_date" 
    ordering = ["-pub_date"]

    
    fieldsets = [
        (None, {
            "fields": ["question_text", "tags"]
        }),
        ("Publication", {
            "fields": ["pub_date"],
            "classes": ["collapse"],
            "description": "Control when this question appears publicly."
        }),
    ]
    inlines = [ChoiceInline]
    filter_horizontal = ["tags"]  

    
    def choice_count(self, obj):
        return obj.choice_set.count()
    choice_count.short_description = "Number of Choices"

    
    actions = ["publish_now"]

    def publish_now(self, request, queryset):
        updated = queryset.update(pub_date=timezone.now())
        self.message_user(
            request,
            f"{updated} question(s) were successfully published right now."
        )
    publish_now.short_description = "Publish selected questions now"


# Registries for the remaining dashboard models (Tags and User Profiles)
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "location"]
    raw_id_fields = ["questions_voted"]  


# Standalone Choice register fallback line
admin.site.register(Choice)
