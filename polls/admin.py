from django.contrib import admin
from django.utils import timezone
from .models import Question, Choice, Tag, UserProfile

# ==============================================================================
# 🗂️ 1. INLINE GRID CONFIGURATION (Nested inside Question forms)
# ==============================================================================
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2  # Shows 2 blank rows out of the box instead of 3
    fields = ["choice_text", "votes"]
    readonly_fields = ["votes"]  # 🔒 Safety lock: Admins cannot alter user vote counts!


# ==============================================================================
# 🗂️ 2. CUSTOM SIDEBAR FILTER CONFIGURATION
# ==============================================================================
class HasChoicesFilter(admin.SimpleListFilter):
    title = "has choices"
    parameter_name = "has_choices"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Has choices"),
            ("no", "No choices"),
        ]

    def queryset(self, request, queryset):
        # 🎯 FIXED: Uses 'choice_set' to match your exact database relationship
        if self.value() == "yes":
            return queryset.filter(choice_set__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(choice_set__isnull=True)
        return queryset


# ==============================================================================
# 🗂️ 3. QUESTION MASTER CONTROL CONTROL PANEL
# ==============================================================================
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    # --- Master Catalog List Page Configurations ---
    list_display = [
        "question_text",
        "pub_date",
        "was_published_recently",
        "choice_count",  # Custom dynamic count column
    ]
    list_filter = ["pub_date", "tags", HasChoicesFilter]  # Combined your filters!
    search_fields = ["question_text"]
    date_hierarchy = "pub_date"  # ⚡ Adds timeline navigation drilldown bars!
    ordering = ["-pub_date"]

    # --- Individual Form Editing Page Configurations ---
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
    filter_horizontal = ["tags"]  # ⚡ Adds gorgeous side-by-side arrow selector boxes for tags!

    # --- Custom Dynamic Column Method ---
    def choice_count(self, obj):
        # 🎯 FIXED: Uses 'choice_set' to accurately calculate answers in memory
        return obj.choice_set.count()
    choice_count.short_description = "Number of Choices"

    # --- Bulk Dropdown Action Manager ---
    actions = ["publish_now"]

    def publish_now(self, request, queryset):
        updated = queryset.update(pub_date=timezone.now())
        self.message_user(
            request,
            f"{updated} question(s) were successfully published right now."
        )
    publish_now.short_description = "Publish selected questions now"


# ==============================================================================
# 🗂️ 4. ADDITIONAL MODEL PANEL REGISTRIES
# ==============================================================================
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "location"]
    raw_id_fields = ["questions_voted"]  # ⚡ Performance saver for large records


# Standalone Choice register fallback line
admin.site.register(Choice)
