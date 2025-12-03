from django.core.management.base import BaseCommand
from django.utils import timezone
from exams.models import SpecialCourse, SpecialEnrollment

class Command(BaseCommand):
    help = 'Finalize overdue exams (submit for users who did not submit)'

    def handle(self, *args, **options):
        now = timezone.now()
        due_courses = SpecialCourse.objects.filter(end_time__lt=now)
        count = 0
        for c in due_courses:
            enrollments = SpecialEnrollment.objects.filter(course=c, submitted=False)
            for e in enrollments:
                total_possible = 0
                total_score = 0
                for q in c.questions.all():
                    total_possible += q.mark
                    ans = e.answers.filter(question=q).first()
                    if ans and ans.choice and ans.choice.is_correct:
                        total_score += q.mark
                e.score = (total_score / total_possible) * 100 if total_possible else 0
                e.submitted = True
                e.submitted_at = now
                e.save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Finalized {count} enrollments'))
