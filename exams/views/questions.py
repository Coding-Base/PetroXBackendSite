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
        """
        Split extracted text into individual question blocks.
        Handles various question numbering formats.
        """
        # Normalize text for consistent parsing
        text = re.sub(r'\r\n', '\n', text)  # Standardize line endings
        text = re.sub(r' +', ' ', text)      # Collapse multiple spaces
        text = text.strip()
        
        # If text is empty, return empty list
        if not text:
            return []
        
        # More flexible splitting that handles various question numbering formats:
        # 1. 1), 1., 1: followed by space(s)
        # 2. (1), (1), (1. followed by space(s)
        # 3. Multiple spaces or newlines before number
        question_split_pattern = r'\n\s*(?:^|\n)(?:\d+[.):,]|\(\d+\)|\)?\s*\d+[\s.]|Q\d*[.):,])\s+'
        
        # Split on question boundaries
        question_blocks = re.split(question_split_pattern, text, flags=re.MULTILINE)
        
        # Filter and process question blocks
        questions = []
        for block in question_blocks:
            block = block.strip()
            
            # Skip empty blocks and blocks that are too short
            if not block or len(block) < 5:
                continue
            
            # Skip blocks that look like headers or page markers
            if len(block) < 20 and block.isupper():
                continue
            
            try:
                question_data = self.parse_question_block(block)
                
                # Only add if we have meaningful content
                if question_data.get('text') and len(question_data.get('text', '')) > 5:
                    questions.append(question_data)
            except Exception as e:
                logger.warning(f"Error parsing question block: {str(e)}")
                # Still capture the block even if parsing partially fails
                questions.append({
                    "text": block[:150].strip(),
                    "optionA": "",
                    "optionB": "",
                    "optionC": "",
                    "optionD": "",
                    "correct_answer": ""
                })
        
        return questions

    def parse_question_block(self, block):
        """
        Robustly parse a question block to extract question text, options, and answer.
        Handles various PDF formatting styles.
        """
        question_text = block.strip()
        options = {'A': '', 'B': '', 'C': '', 'D': ''}
        answer = ''
        
        # Step 1: Extract answer first (it's often at the end or marked clearly)
        answer = self._extract_answer(block)
        
        # Step 2: Robustly extract all options with flexible patterns
        option_dict = self._extract_all_options(block)
        options.update(option_dict)
        
        # Step 3: Extract question text (everything before first option)
        if option_dict:
            question_text = self._extract_question_text(block, option_dict)
        
        return {
            "text": question_text.strip(),
            "optionA": options.get('A', '').strip(),
            "optionB": options.get('B', '').strip(),
            "optionC": options.get('C', '').strip(),
            "optionD": options.get('D', '').strip(),
            "correct_answer": answer
        }
    
    def _extract_answer(self, text):
        """
        Extract the correct answer from various formats:
        - Answer: A
        - Correct answer: B
        - Ans: C
        - Answer is D
        - [D]
        - etc.
        """
        # Try multiple patterns for answer extraction
        patterns = [
            r'(?:Answer|Correct\s+answer|Ans)[:\s]+([A-D])',  # Answer: A or Correct answer: B
            r'(?:answer|Answer)\s+(?:is|=)\s*([A-D])',  # Answer is A
            r'\[([A-D])\]\s*(?:\n|$)',  # [A] on its own line
            r'(?:^|\n)\s*([A-D])\s*(?:\n|$)',  # Single letter on own line (after other content)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).upper()
        
        return ''
    
    def _extract_all_options(self, text):
        """
        Extract options (A, B, C, D) with flexible pattern matching.
        Handles various formatting styles:
        - A) option text
        - A. option text
        - A: option text
        - A option text
        - a) option text (case insensitive)
        """
        options = {}
        
        # More flexible option patterns that handle inline and newline formats
        option_patterns = [
            # Standard formats: A) text, A. text, A: text
            r'^\s*([A-D])[.):]\s*(.+?)(?=^\s*[A-D][.):]\s|^[A-D]\s|$)',
            # Inline format: A text (space separated)
            r'^\s*([A-D])\s+([^A-D][^A-D]*?)(?=^\s*[A-D][.):]\s|^\s*[A-D]\s|$)',
        ]
        
        for option_letter in ['A', 'B', 'C', 'D']:
            found = False
            
            # Try different variations of finding option letter
            for pattern in [
                rf'(?:^|\n)\s*{option_letter}[.):]\s*(.+?)(?=(?:^|\n)\s*[A-D][.):]\s|(?:^|\n)\s*[A-D]\s|[Aa]nswer:|$)',
                rf'(?:^|\n)\s*{option_letter}\s+(.+?)(?=(?:^|\n)\s*[A-D][.):]\s|(?:^|\n)\s*[A-D]\s|[Aa]nswer:|$)',
            ]:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                if match and match.group(1):
                    option_text = match.group(1).strip()
                    # Clean up the option text - remove continuation markers
                    option_text = re.sub(r'\n\s+', ' ', option_text)  # Replace newlines with spaces
                    option_text = option_text.split('\n')[0].strip()  # Get first line only
                    
                    if option_text and len(option_text) > 0:
                        options[option_letter] = option_text
                        found = True
                        break
            
            # If not found, try a more lenient search
            if not found:
                # Look for letter followed by any content that doesn't look like the next option
                lenient_pattern = rf'{option_letter}[.):]\s*([^\n{{0,200}}])'
                match = re.search(lenient_pattern, text)
                if match:
                    option_text = match.group(1).strip()
                    # Clean up
                    option_text = re.sub(r'^[A-D][.):]\s*', '', option_text).strip()
                    option_text = option_text.split('\n')[0].split(option_letter.upper() if option_letter < 'D' else 'Answer')[0].strip()
                    if option_text:
                        options[option_letter] = option_text
        
        return options
    
    def _extract_question_text(self, block, option_dict):
        """
        Extract question text by finding the content before the first option marker.
        """
        # Find the position of the first option
        first_option_pos = float('inf')
        first_option_letter = None
        
        for letter in ['A', 'B', 'C', 'D']:
            # Look for pattern like "A)" or "A." or "A:"
            for sep in ['.', ')', ':']:
                pattern = f'{letter}{sep}'
                pos = block.find(pattern)
                if pos != -1 and pos < first_option_pos:
                    first_option_pos = pos
                    first_option_letter = letter
        
        if first_option_pos != float('inf'):
            question_text = block[:first_option_pos].strip()
        else:
            # No options found, return whole block
            question_text = block.strip()
        
        # Clean up question text - remove extra whitespace but preserve structure
        question_text = re.sub(r'\n+', ' ', question_text)
        question_text = re.sub(r'\s+', ' ', question_text).strip()
        
        return question_text

class UploadPassQuestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        course_id = request.data.get('course_id')
        year = request.data.get('year')
        questions_data = request.data.get('questions', [])
        question_type = request.data.get('question_type', 'multichoice')
        
        if not course_id or not questions_data:
            return Response(
                {"error": "Missing required fields (course_id or questions)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        course = get_object_or_404(Course, id=course_id)
        
        # Check if questions already exist for this course/year
        if year and Question.objects.filter(course=course, year=year).exists():
            return Response(
                {"error": f"Past questions for {course.name} ({year}) already exist"},
                status=status.HTTP_409_CONFLICT
            )
        
        created_count = 0
        errors = []
        
        for i, q in enumerate(questions_data):
            if q.get('text'):
                try:
                    # For theory questions, skip options and answer
                    if question_type == 'theory':
                        Question.objects.create(
                            course=course,
                            year=year,
                            question_text=q['text'],
                            option_a='',
                            option_b='',
                            option_c='',
                            option_d='',
                            correct_option='',
                            status='pending',
                            uploaded_by=request.user
                        )
                    else:
                        Question.objects.create(
                            course=course,
                            year=year,
                            question_text=q['text'],
                            option_a=q.get('optionA', '').strip(),
                            option_b=q.get('optionB', '').strip(),
                            option_c=q.get('optionC', '').strip(),
                            option_d=q.get('optionD', '').strip(),
                            correct_option=q.get('correct_answer', '').upper(),
                            status='pending',
                            uploaded_by=request.user
                        )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Question {i+1}: {str(e)}")
        
        if created_count > 0:
            self.notify_admins(request.user, course, created_count, year)
            
        response = {
            "message": f"{created_count} questions uploaded for review",
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
