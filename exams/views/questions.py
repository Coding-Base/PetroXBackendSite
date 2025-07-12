import random
import re
import PyPDF2
from docx import Document
from io import BytesIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from ..models import Course, Question, User
from ..serializers import QuestionSerializer, PreviewPassQuestionsSerializer

class AddQuestionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class QuestionApprovalView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        pending_questions = Question.objects.filter(status='pending')
        data = [
            {
                "id": q.id,
                "course": q.course.name,
                "question_text": q.question_text,
                "status": q.status,
            }
            for q in pending_questions
        ]
        return Response(data)

    def patch(self, request, question_id):
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"detail": "Question not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")
        if new_status not in ["approved", "rejected"]:
            return Response(
                {"detail": "Invalid status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        question.status = new_status
        question.save()
        return Response(
            {"detail": f"Question {question_id} status updated to {new_status}."}
        )

class PreviewPassQuestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            raise ParseError("No file provided.")
        
        text = self.extract_text(file)
        questions = self.parse_questions(text)
        
        return Response({
            'questions': questions,
            'filename': file.name
        }, status=200)
    
    def extract_text(self, file):
        filename = file.name.lower()
        file_content = file.read()
        file.seek(0)
        
        if filename.endswith('.pdf'):
            try:
                reader = PyPDF2.PdfReader(BytesIO(file_content))
                return "\n".join([page.extract_text() for page in reader.pages])
            except Exception as e:
                raise ParseError(f"PDF processing error: {str(e)}")
                
        elif filename.endswith('.docx'):
            try:
                doc = Document(BytesIO(file_content))
                return "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                raise ParseError(f"DOCX processing error: {str(e)}")
                
        elif filename.endswith('.txt'):
            try:
                return file_content.decode('utf-8')
            except Exception as e:
                raise ParseError(f"Text file processing error: {str(e)}")
                
        else:
            raise ParseError("Unsupported file format. Use PDF, DOCX, or TXT")

    def parse_questions(self, text):
        # Normalize text for consistent parsing
        text = re.sub(r'\r\n', '\n', text)  # Standardize line endings
        text = re.sub(r' +', ' ', text)      # Collapse multiple spaces
        
        # Improved pattern to handle different formats
        pattern = r'(\d+[.)]\s*(.*?))(?:\s*([aA][.)]\s*(.*?))?\s*([bB][.)]\s*(.*?))?\s*([cC][.)]\s*(.*?))?\s*([dD][.)]\s*(.*?))?(\s*Answer:\s*([A-Da-d]))?'
        
        matches = re.findall(pattern, text, re.DOTALL)
        
        questions = []
        for match in matches:
            # Extract components from match groups
            question_text = match[1].strip()
            option_a = match[3] if match[3] else ''
            option_b = match[5] if match[5] else ''
            option_c = match[7] if match[7] else ''
            option_d = match[9] if match[9] else ''
            answer = match[10].upper() if match[10] else ''
            
            # Clean and format options
            options = {
                'A': re.sub(r'^\s*[aA][.)]\s*', '', option_a).strip(),
                'B': re.sub(r'^\s*[bB][.)]\s*', '', option_b).strip(),
                'C': re.sub(r'^\s*[cC][.)]\s*', '', option_c).strip(),
                'D': re.sub(r'^\s*[dD][.)]\s*', '', option_d).strip(),
            }
            
            questions.append({
                "text": question_text,
                "A": options['A'],
                "B": options['B'],
                "C": options['C'],
                "D": options['D'],
                "answer": answer
            })
        
        # If no questions found, fallback to theory mode
        if not questions:
            return [{
                'text': text,
                'A': '',
                'B': '',
                'C': '',
                'D': '',
                'answer': ''
            }]
        
        return questions

class UploadPassQuestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        course_id = request.data.get('course_id')
        year = request.data.get('year')
        questions_data = request.data.get('questions', [])
        
        if not course_id or not questions_data or not year:
            return Response(
                {"error": "Missing required fields (course_id, year, or questions)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        course = get_object_or_404(Course, id=course_id)
        
        # Check if questions already exist for this course/year
        if Question.objects.filter(course=course, year=year).exists():
            return Response(
                {"error": f"Past questions for {course.name} ({year}) already exist"},
                status=status.HTTP_409_CONFLICT
            )
        
        created_count = 0
        
        for q in questions_data:
            if q.get('text'):
                # Ensure options are properly formatted
                option_a = q.get('A', '').strip()
                option_b = q.get('B', '').strip()
                option_c = q.get('C', '').strip()
                option_d = q.get('D', '').strip()
                
                Question.objects.create(
                    course=course,
                    year=year,
                    question_text=q['text'],
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_option=q.get('answer', '').upper(),
                    status='pending',
                    uploaded_by=request.user
                )
                created_count += 1
                
        self.notify_admins(request.user, course, created_count, year)
            
        return Response({
            "message": f"{created_count} questions for {year} uploaded for review",
            "course": course.name,
            "year": year
        }, status=status.HTTP_201_CREATED)
    
    def notify_admins(self, user, course, count, year):
        admin_emails = User.objects.filter(
            is_staff=True
        ).values_list('email', flat=True)
        
        if admin_emails and count > 0:
            subject = f"New {year} Questions Pending Approval for {course.name}"
            message = f"User {user.username} uploaded {count} questions for {course.name} ({year}). Please review them in the admin panel."
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    admin_emails,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send email notification: {str(e)}")
