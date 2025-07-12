import re
import PyPDF2
from docx import Document
from io import BytesIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ParseError
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
import logging
from ..models import Course, Question, User

logger = logging.getLogger(__name__)

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
        
        try:
            text = self.extract_text(file)
            questions = self.parse_questions(text)
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return Response(
                {"error": f"Error processing file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        text = text.strip()
        
        # If text is empty, return empty list
        if not text:
            return []
        
        # Split text into individual question blocks
        # This regex looks for question numbers like "1.", "2)", "(3)", etc.
        question_blocks = re.split(r'\n\s*(\d+[.)]|\(\d+\))\s*', text)
        
        # If we didn't find any question blocks, treat the whole text as one question
        if len(question_blocks) <= 1:
            return [self.parse_question_block(text)]
        
        # The first element is usually text before first question, which we skip
        questions = []
        for i in range(1, len(question_blocks), 2):
            question_number = question_blocks[i].strip()
            question_content = question_blocks[i+1].strip()
            
            # Skip empty content
            if not question_content:
                continue
                
            try:
                question_data = self.parse_question_block(question_content)
                questions.append(question_data)
            except Exception as e:
                logger.error(f"Error parsing question {question_number}: {str(e)}")
                questions.append({
                    "text": f"Error parsing question: {question_content[:200]}...",
                    "A": "",
                    "B": "",
                    "C": "",
                    "D": "",
                    "answer": ""
                })
        
        return questions

    def parse_question_block(self, block):
        # Extract question text (everything before first option)
        question_text = block
        options = {'A': '', 'B': '', 'C': '', 'D': ''}
        answer = ''
        
        # Try to find options in the block
        option_pattern = r'\n\s*([a-dA-D])[.)]\s*(.*?)(?=\n\s*[a-dA-D][.)]|\n\s*Answer:|\Z)'
        option_matches = re.findall(option_pattern, block, re.DOTALL | re.IGNORECASE)
        
        if option_matches:
            # Extract question text (everything before first option)
            first_option_pos = block.find(option_matches[0][0] + ')') or block.find(option_matches[0][0] + '.')
            if first_option_pos != -1:
                question_text = block[:first_option_pos].strip()
            
            # Process found options
            for letter, option_text in option_matches:
                letter = letter.upper()
                if letter in options:
                    # Remove option prefix if it exists
                    clean_text = re.sub(r'^\s*[a-dA-D][.)]\s*', '', option_text).strip()
                    options[letter] = clean_text
        
        # Look for answer pattern (case-insensitive)
        answer_match = re.search(r'Answer:\s*([a-dA-D])', block)
        if answer_match:
            answer = answer_match.group(1).upper()
        
        return {
            "text": question_text,
            "A": options['A'],
            "B": options['B'],
            "C": options['C'],
            "D": options['D'],
            "answer": answer
        }

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
        errors = []
        
        for i, q in enumerate(questions_data):
            if q.get('text'):
                try:
                    Question.objects.create(
                        course=course,
                        year=year,
                        question_text=q['text'],
                        option_a=q.get('A', '').strip(),
                        option_b=q.get('B', '').strip(),
                        option_c=q.get('C', '').strip(),
                        option_d=q.get('D', '').strip(),
                        correct_option=q.get('answer', '').upper(),
                        status='pending',
                        uploaded_by=request.user
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Question {i+1}: {str(e)}")
        
        if created_count > 0:
            self.notify_admins(request.user, course, created_count, year)
            
        response = {
            "message": f"{created_count} questions for {year} uploaded for review",
            "course": course.name,
            "year": year
        }
        
        if errors:
            response["errors"] = errors
            
        return Response(response, status=status.HTTP_201_CREATED)
    
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
                logger.error(f"Failed to send email notification: {str(e)}")
