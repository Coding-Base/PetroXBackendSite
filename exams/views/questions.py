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
        
        # Try parsing as multiple-choice first
        questions = self.parse_multichoice_questions(text)
        
        # If no multiple-choice questions found, parse as theory questions
        if not questions or all(not q['A'] for q in questions):
            raw_qs = self.split_questions(text)
            questions = []
            for q in raw_qs:
                parts = self.split_parts(q['body'])
                if parts:
                    # Theory question with parts
                    question_text = " ".join([f"{lbl}) {txt}" for lbl, txt in parts])
                else:
                    # Single theory question
                    question_text = q['body']
                questions.append({
                    'text': question_text,
                    'A': '',
                    'B': '',
                    'C': '',
                    'D': '',
                    'answer': ''
                })
        else:
            # Ensure multiple-choice questions have all fields
            for q in questions:
                q['text'] = q.get('text', '')
                q['A'] = q.get('A', '')
                q['B'] = q.get('B', '')
                q['C'] = q.get('C', '')
                q['D'] = q.get('D', '')
                q['answer'] = q.get('answer', '').upper()
        
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

    def parse_multichoice_questions(self, text):
        pattern = r"""
            ^\s*(\d+)[\.\)]\s*                # Question number
            (.*?)\s*                          # Question text
            (?:\n\s*a[\)\.]?\s*(.*?)\s*)?     # Option a (optional)
            (?:\n\s*b[\)\.]?\s*(.*?)\s*)?     # Option b (optional)
            (?:\n\s*c[\)\.]?\s*(.*?)\s*)?     # Option c (optional)
            (?:\n\s*d[\)\.]?\s*(.*?)\s*)?     # Option d (optional)
            (?:\n\s*Answer:\s*([a-dA-D])?\s*)? # Optional answer
            (?=\n\s*\d+[\.\)]|\Z)             # Lookahead for next question or end
        """
        
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.VERBOSE)
        
        questions = []
        for m in matches:
            questions.append({
                "number": m[0],
                "text": m[1].strip(),
                "A": m[2].strip(),
                "B": m[3].strip(),
                "C": m[4].strip(),
                "D": m[5].strip(),
                "answer": m[6].upper() if m[6] else ""
            })
        
        return questions if questions else [{'text': text, 'A': '', 'B': '', 'C': '', 'D': '', 'answer': ''}]

    def split_questions(self, text):
        # Split text into individual questions based on question numbers
        # Assuming questions start with a number followed by a dot or in parentheses
        pattern = r'(?:^|\n)(\(\d+\)|\d+[\.\)])\s*(.*?)(?=\n\(\d+\)|\n\d+[\.\)]|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        return [{'number': match[0], 'body': match[1].strip()} for match in matches]

    def split_parts(self, body):
        # Split question body into parts (e.g., a), b), etc.)
        pattern = r'([a-zA-Z]\))\s*(.*?)(?=[a-zA-Z]\)|$)'
        matches = re.findall(pattern, body, re.DOTALL)
        return [(match[0], match[1].strip()) for match in matches]

class UploadPassQuestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        course_id = request.data.get('course_id')
        year = request.data.get('year')  # Get year from request
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
                Question.objects.create(
                    course=course,
                    year=year,  # Add year to question
                    question_text=q['text'],
                    option_a=q.get('A', ''),
                    option_b=q.get('B', ''),
                    option_c=q.get('C', ''),
                    option_d=q.get('D', ''),
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
            subjectNOTE = f"New {year} Questions Pending Approval for {course.name}"
            message = f"User {user.username} uploaded {count} questions for {course.name} ({year}). Please review them in the admin panel."
            
            try:
                send_mail(
                    subjectNOTE,
                    message,
                    settings.EMAIL_HOST_USER,
                    admin_emails,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send email notification: {str(e)}")