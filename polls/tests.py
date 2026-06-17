from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
import datetime
from .models import Question, Choice, Tag
from django.contrib.auth.models import User
# Create your tests here.


class QuestionModelTests(TestCase):
    def setUp(self):
        self.future_question = Question.objects.create(
            question_text = "Future Question?",
            pub_date = timezone.now() + datetime.timedelta(days=30)
        )
        self.old_question = Question.objects.create(
            question_text = "Old Question?",
            pub_date = timezone.now() - datetime.timedelta(days=1,seconds=1)
        )
        self.recent_question = Question.objects.create(
            question_text = "Recent Question?",
            pub_date = timezone.now() - datetime.timedelta(hours=23,minutes=59,seconds=59)
        )

    def test_was_published_recently_with_future_question(self):
        self.assertIs(self.future_question.was_published_recently(),False)

    def test_was_published_recently_with_old_questions(self):
        self.assertIs(self.old_question.was_published_recently(),False)

    def test_was_published_recently_with_recent_questions(self):
        self.assertIs(self.recent_question.was_published_recently(),True)

    def test_question_str_representation(self):
        self.assertEqual(str(self.recent_question),"Recent Question?")

class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response,"No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"],[])

    def test_no_future_question_displayed_on_index(self):
        Question.objects.create(
            question_text = "Question 1?",
            pub_date = timezone.now() + datetime.timedelta(days=30)
        )
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"],[])
        self.assertContains(response,"No polls are available.")

    def test_past_question_on_index(self):
        question = Question.objects.create(
            question_text="Past question?",
            pub_date=timezone.now() - datetime.timedelta(days=30)
        )
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"],[question])
        self.assertEqual(response.status_code, 200)

    def test_display_5_question_on_index(self):
        for i in range(7):
            Question.objects.create(
                question_text=f"Past question{i}?",
                pub_date=timezone.now() - datetime.timedelta(days=i)
            )
        response = self.client.get(reverse("polls:index"))
        visible_questions = response.context["latest_question_list"]
        self.assertEqual(len(visible_questions),5)
        for i in range(len(visible_questions)-1):
            current_question = visible_questions[i]
            next_question = visible_questions[i+1]

            self.assertGreater(
                current_question.pub_date,
                next_question.pub_date
                , msg=f"Sorting broken! '{current_question}' is not newer than '{next_question}'."
            )

class ProtectedViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
            email="test@example.com"
        )
        self.question = Question.objects.create(
            question_text="Test question?",
            pub_date=timezone.now() - datetime.timedelta(days=1)
        )

    def test_create_question_redirects_anonymous_user(self):
        url = reverse("polls:create_question")
        response = self.client.get(url)
        self.assertEqual(response.status_code,302)
        login_url = reverse("login")
        self.assertRedirects(
            response,
            f"{login_url}?next={url}"
        )

    def test_create_question_accessible_to_logged_in_user(self):
        self.client.login(
            username="testuser",
            password="testpassword123"
        )
        response = self.client.get(reverse("polls:create_question"))
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response,"polls/create_question.html")

    def test_logged_in_user_can_create_question(self):
        self.client.login(
            username="testuser",
            password="testpassword123"
        )
        self.client.post(
            reverse("polls:create_question"),
            {
                "question_text" : "A brand new question?",
                "pub_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                "choice_set-TOTAL_FORMS": "3",
                "choice_set-INITIAL_FORMS": "0",
                "choice_set-MIN_NUM_FORMS": "0",
                "choice_set-MAX_NUM_FORMS": "1000",
                
                "choice_set-0-choice_text": "Option One",
                "choice_set-1-choice_text": "Option Two",
                "choice_set-2-choice_text": "Option Three",

            }
        )
        self.assertEqual(Question.objects.count(),2)
        new_question = Question.objects.latest("pub_date")
        self.assertEqual(new_question.question_text,"A brand new question?")

    def test_anonymous_user_cannot_vote(self):
        response = self.client.post(
            reverse("polls:vote",args=[self.question.id]),
            {"choice":"1"}
        )
        self.assertEqual(response.status_code,302)

class VoteViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="voter",
            password="password123"
        )

        self.question = Question.objects.create(
            question_text = "Best language?",
            pub_date = timezone.now() - datetime.timedelta(days=1)
        )
        self.choice1 = Choice.objects.create(
            question = self.question,
            choice_text="Python",
            votes=0
        )
        self.choice2 = Choice.objects.create(
            question=self.question,
            choice_text="JavaScript",
            votes=0
        )

    def test_voting_increments_voting_count(self):
        self.client.login(username="voter",password="password123")
        self.client.post(
            reverse("polls:vote" ,args=[self.question.id]),{"choice": self.choice1.id}
        )
        self.choice1.refresh_from_db()
        self.assertEqual(self.choice1.votes,1)

    def test_voting_redirects_to_result(self):
        self.client.login(username="voter",password="password123")
        response=self.client.post(
            reverse("polls:vote" ,args=[self.question.id]),{"choice": self.choice1.id}
        )
        self.assertRedirects(response,reverse("polls:results", args=(self.question.id,)))

    def test_voting_with_no_choice_selected(self):
        self.client.login(username="voter",password="password123")
        response=self.client.post(
            reverse("polls:vote" ,args=[self.question.id]),{}
        )
        self.assertEqual(response.status_code,200)
        self.assertContains(response, "You didn&#x27;t select a choice.")

    def test_voting_with_invalid_choice_id(self):
        self.client.login(username="voter",password="password123")
        response=self.client.post(
            reverse("polls:vote" ,args=[self.question.id]),{"choice": 99999}
        )
        self.assertEqual(response.status_code,200)
        self.assertContains(response, "You didn&#x27;t select a choice.")

class QuestionDetailViewTests(TestCase):
    def setUp(self):
        self.question = Question.objects.create(
            question_text="Security Test Question?",
            pub_date=timezone.now() - datetime.timedelta(days=1)
        )

    def test_future_question_returns_404(self):
        question = Question.objects.create(
            question_text = "Future Poll?",
            pub_date = timezone.now() + datetime.timedelta(days=5)
        )
        response = self.client.get(reverse("polls:detail",args=[question.id]))
        self.assertEqual(response.status_code,404)

    def test_past_question_displays_correctly(self):
        response = self.client.get(reverse("polls:detail",args=[self.question.id]))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,self.question.question_text)
        self.assertTemplateUsed(response,"polls/detail.html")

    def test_nonexistent_question_returns_404(self):
        response = self.client.get(reverse("polls:detail",args=[9999]))
        self.assertEqual(response.status_code,404)

    def test_anonymous_user_cannot_access_edit_page(self):
        url = reverse("polls:update_question",args=[self.question.id])
        response = self.client.get(url)
        login_url = reverse("login")
        self.assertRedirects(response, f"{login_url}?next={url}")
        self.assertEqual(response.status_code,302)

    def test_anonymous_user_cannot_access_delete_page(self):
        url = reverse("polls:delete_question",args=[self.question.id])
        response = self.client.get(url)
        login_url = reverse("login")
        self.assertRedirects(response, f"{login_url}?next={url}")
        self.assertEqual(response.status_code,302)
