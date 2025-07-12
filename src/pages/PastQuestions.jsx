import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { fetchCourses } from '@/api/index';

const UploadPassQuestions = () => {
  const [step, setStep] = useState(1);
  const [questionType, setQuestionType] = useState('multichoice');
  const [file, setFile] = useState(null);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [year, setYear] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [uploadStatus, setUploadStatus] = useState(null);
  const [parsedQuestions, setParsedQuestions] = useState([]);
  const [courses, setCourses] = useState([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(true);
  const [courseError, setCourseError] = useState('');

  // Generate years from current year back 30 years
  const currentYear = new Date().getFullYear();
  const years = Array.from({length: 30}, (_, i) => currentYear - i);

  // Fetch courses on component mount
  useEffect(() => {
    const loadCourses = async () => {
      try {
        setIsLoadingCourses(true);
        const response = await fetchCourses();
        // If your API returns { data: [...] }
        const courseArr = Array.isArray(response.data) ? response.data : response;
        setCourses(courseArr);
      } catch (err) {
        console.error('Failed to fetch courses:', err);
        setCourseError('Failed to load courses. Please try again later.');
        setCourses([]);
      } finally {
        setIsLoadingCourses(false);
      }
    };

    loadCourses();
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const validTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
      ];
      if (!validTypes.includes(selectedFile.type)) {
        setMessage({
          text: 'Invalid file type. Please upload PDF, DOCX, or TXT.',
          type: 'error'
        });
        return;
      }
      setFile(selectedFile);
      setMessage({ text: '', type: '' });
    }
  };

  const handleQuestionChange = (index, field, value) => {
    const updatedQuestions = [...parsedQuestions];
    updatedQuestions[index] = {
      ...updatedQuestions[index],
      [field]: value
    };
    setParsedQuestions(updatedQuestions);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (step === 1 && !year) {
      setMessage({ text: 'Please select a year', type: 'error' });
      return;
    }

    if (step === 1) {
      if (!file) {
        setMessage({ text: 'Please select a file', type: 'error' });
        return;
      }
      if (!selectedCourse) {
        setMessage({ text: 'Please select a course', type: 'error' });
        return;
      }
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('question_type', questionType);
      formData.append('year', year);

      setIsLoading(true);
      setMessage({ text: '', type: '' });
      try {
        const response = await axios.post(
          'https://petroxtestbackend.onrender.com/api/preview-pass-questions/', 
          formData, 
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        const questionsWithIds = response.data.questions.map(q => ({
          ...q,
          id: Math.random().toString(36).substr(2, 9)
        }));
        
        setParsedQuestions(questionsWithIds);
        setStep(2);
      } catch (error) {
        const errorMsg = error.response?.data?.error || 
                        error.response?.data?.message || 
                        'Failed to parse file. Please check the format and try again.';
        setMessage({ text: errorMsg, type: 'error' });
      } finally {
        setIsLoading(false);
      }
    } else {
      setIsLoading(true);
      setMessage({ text: '', type: '' });
      
      try {
        // Validate all questions are filled
        const hasEmptyQuestions = parsedQuestions.some(q => {
          if (!q.text) return true;
          if (questionType === 'multichoice') {
            return !q.A || !q.B || !q.C || !q.D || !q.answer;
          }
          return false;
        });
        
        if (hasEmptyQuestions) {
          setMessage({ 
            text: 'Please fill all question fields and ensure answers are selected', 
            type: 'error' 
          });
          setIsLoading(false);
          return;
        }
        
        // Format questions for backend
        const formattedQuestions = parsedQuestions.map(q => {
          const baseQuestion = {
            text: q.text,
            question_type: questionType
          };
          
          if (questionType === 'multichoice') {
            return {
              ...baseQuestion,
              optionA: q.A,
              optionB: q.B,
              optionC: q.C,
              optionD: q.D,
              correct_answer: q.answer
            };
          }
          return baseQuestion;
        });

        const response = await axios.post(
          'https://petroxtestbackend.onrender.com/api/upload-pass-questions/', 
          {
            course_id: selectedCourse,
            year: year,
            questions: formattedQuestions,
            question_type: questionType
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        setMessage({ 
          text: response.data.message || 'Questions submitted successfully! They are pending admin approval.',
          type: 'success'
        });
        
        setUploadStatus({
          count: parsedQuestions.length,
          year: year,
          course: courses.find(c => c.id == selectedCourse)?.name || 'Unknown Course',
          filename: file.name
        });
        
        setFile(null);
        setSelectedCourse('');
        setYear('');
        setStep(1);
        setParsedQuestions([]);
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) fileInput.value = '';
      } catch (error) {
        console.error('Submission error:', {
          status: error.response?.status,
          data: error.response?.data,
          course_id: selectedCourse,
          year: year,
          question_count: parsedQuestions.length
        });
        
        if (error.response?.status === 409) {
          setMessage({ 
            text: error.response.data.error || 'Past questions for this year already exist', 
            type: 'error' 
          });
        } else {
          const errorMsg = error.response?.data?.error || 
                          error.response?.data?.message || 
                          'Submission failed. Please try again.';
          setMessage({ text: errorMsg, type: 'error' });
        }
      } finally {
        setIsLoading(false);
      }
    }
  };

  const renderQuestionEditor = () => (
    <div className="mt-6">
      <h2 className="text-lg sm:text-xl font-semibold mb-4">Review and Edit Questions</h2>
      <p className="text-xs sm:text-sm text-gray-600 mb-4">
        Please review the parsed questions and make any necessary corrections before submitting.
      </p>
      <div className="max-h-[400px] overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-[600px] w-full bg-white text-xs sm:text-sm">
          <thead className="sticky top-0 bg-gray-50 z-10">
            <tr>
              <th className="py-2 px-2 sm:py-3 sm:px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Question</th>
              <th className="py-2 px-2 sm:py-3 sm:px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Option A</th>
              <th className="py-2 px-2 sm:py-3 sm:px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Option B</th>
              <th className="py-2 px-2 sm:py-3 sm:px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Option C</th>
              <th className="py-2 px-2 sm:py-3 sm:px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Option D</th>
              <th className="py-2 px-2 sm:py-3 sm:px-4 text-left font-medium text-gray-500 uppercase tracking-wider">Correct Answer</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {parsedQuestions.map((q, index) => (
              <tr key={q.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="py-2 px-2 sm:py-3 sm:px-4">
                  <textarea
                    value={q.text}
                    onChange={(e) => handleQuestionChange(index, 'text', e.target.value)}
                    className="w-full p-2 border rounded text-xs sm:text-sm h-20 sm:h-24"
                    placeholder="Question text"
                  />
                </td>
                <td className="py-2 px-2 sm:py-3 sm:px-4">
                  <input
                    type="text"
                    value={q.A}
                    onChange={(e) => handleQuestionChange(index, 'A', e.target.value)}
                    className="w-full p-2 border rounded text-xs sm:text-sm"
                    placeholder="Option A"
                    disabled={questionType === 'theory'}
                  />
                </td>
                <td className="py-2 px-2 sm:py-3 sm:px-4">
                  <input
                    type="text"
                    value={q.B}
                    onChange={(e) => handleQuestionChange(index, 'B', e.target.value)}
                    className="w-full p-2 border rounded text-xs sm:text-sm"
                    placeholder="Option B"
                    disabled={questionType === 'theory'}
                  />
                </td>
                <td className="py-2 px-2 sm:py-3 sm:px-4">
                  <input
                    type="text"
                    value={q.C}
                    onChange={(e) => handleQuestionChange(index, 'C', e.target.value)}
                    className="w-full p-2 border rounded text-xs sm:text-sm"
                    placeholder="Option C"
                    disabled={questionType === 'theory'}
                  />
                </td>
                <td className="py-2 px-2 sm:py-3 sm:px-4">
                  <input
                    type="text"
                    value={q.D}
                    onChange={(e) => handleQuestionChange(index, 'D', e.target.value)}
                    className="w-full p-2 border rounded text-xs sm:text-sm"
                    placeholder="Option D"
                    disabled={questionType === 'theory'}
                  />
                </td>
                <td className="py-2 px-2 sm:py-3 sm:px-4">
                  <select
                    value={q.answer}
                    onChange={(e) => handleQuestionChange(index, 'answer', e.target.value)}
                    className="w-full p-2 border rounded text-xs sm:text-sm"
                    disabled={questionType === 'theory'}
                  >
                    <option value="">Select</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Button group: sticky on mobile */}
      <div className="mt-4 flex flex-col sm:flex-row gap-2 sm:gap-4 justify-between
        fixed bottom-0 left-0 right-0 bg-white p-2 border-t border-gray-200 z-20 sm:static sm:bg-transparent sm:border-0 sm:p-0">
        <Button
          type="button"
          onClick={() => setStep(1)}
          className="w-full sm:w-auto px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 transition"
        >
          Back to Upload
        </Button>
        <Button
          type="submit"
          disabled={isLoading}
          className={`w-full sm:w-auto px-6 py-2 rounded-lg font-medium text-white transition ${
            isLoading 
              ? 'bg-blue-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isLoading ? 'Submitting...' : 'Submit Questions'}
        </Button>
      </div>
      {/* Add padding to bottom so content is not hidden behind sticky buttons */}
      <div className="h-20 sm:hidden" />
    </div>
  );

  if (isLoadingCourses) {
    return (
      <div className="container bg-gray-50 mx-auto p-4 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
          <p className="mt-4 text-indigo-700">Loading courses...</p>
        </div>
      </div>
    );
  }

  if (courseError) {
    return (
      <div className="container bg-gray-50 mx-auto p-2 sm:p-4">
        <div className="bg-white rounded-lg shadow-md p-4 sm:p-6">
          <div className="rounded-lg bg-red-100 p-4 text-red-700">
            <p className="font-medium">{courseError}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-3 rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container bg-gray-50 mx-auto p-2 sm:p-4">      
      <div className="bg-white rounded-lg shadow-md p-2 sm:p-6">
        <h1 className="text-lg sm:text-2xl font-bold mb-4 sm:mb-6 text-gray-800">
          {step === 1 ? 'Upload Past Questions' : 'Review Questions'}
        </h1>
        
        {step === 1 && (
          <>
            <div className="mb-4 sm:mb-6">
              <h2 className="text-base sm:text-lg font-semibold mb-2 sm:mb-3 text-gray-700">Question Type</h2>
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
                <Button 
                  className={`w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 rounded-lg transition ${
                    questionType === 'multichoice' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 hover:bg-gray-300'
                  }`}
                  onClick={() => setQuestionType('multichoice')}
                >
                  Multiple Choice
                </Button>
                <Button 
                  className={`w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 rounded-lg transition ${
                    questionType === 'theory' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 hover:bg-gray-300'
                  }`}
                  onClick={() => setQuestionType('theory')}
                >
                  Theory Questions
                </Button>
              </div>
              <p className="mt-2 text-xs sm:text-sm text-gray-500">
                Select the type of questions in your file
              </p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                  Year
                </label>
                <select
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className="w-full p-2 sm:p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-xs sm:text-sm"
                  required
                >
                  <option value="">-- Select year --</option>
                  {years.map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                  Select Course
                </label>
                <select
                  value={selectedCourse}
                  onChange={(e) => setSelectedCourse(e.target.value)}
                  className="w-full p-2 sm:p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-xs sm:text-sm"
                  required
                >
                  <option value="">-- Select a course --</option>
                  {courses.map(course => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                  Upload File
                </label>
                <div className="flex flex-col sm:flex-row items-center gap-2 sm:space-x-4">
                  <label className="flex-1 w-full">
                    <div className={`border-2 border-dashed rounded-lg p-3 sm:p-4 text-center cursor-pointer hover:border-blue-400 transition ${
                      file ? 'border-green-500 bg-green-50' : 'border-gray-300'
                    }`}>
                      <input
                        type="file"
                        onChange={handleFileChange}
                        accept=".pdf,.docx,.txt"
                        className="hidden"
                        required
                      />
                      <p className="text-gray-600 text-xs sm:text-sm">
                        {file ? (
                          <span className="font-medium text-green-700">{file.name}</span>
                        ) : (
                          'Click to browse or drag and drop'
                        )}
                      </p>
                      <p className="text-[10px] sm:text-xs text-gray-500 mt-1">
                        Supported formats: PDF, DOCX, TXT
                      </p>
                    </div>
                  </label>
                  {file && (
                    <Button
                      type="button"
                      onClick={() => {
                        setFile(null);
                        document.querySelector('input[type="file"]').value = '';
                      }}
                      className="p-2 text-xs sm:text-base text-red-500 hover:text-red-700"
                    >
                      ✕ Clear
                    </Button>
                  )}
                </div>
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={isLoading || !file || !selectedCourse || !year}
                  className={`w-full py-2 sm:py-3 px-4 rounded-lg font-medium text-white transition text-xs sm:text-base ${
                    isLoading 
                      ? 'bg-blue-400 cursor-not-allowed' 
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    'Parse Questions'
                  )}
                </Button>
              </div>
            </form>
          </>
        )}

        {step === 2 && (
          <form onSubmit={handleSubmit}>
            <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-blue-50 rounded-lg">
              <h3 className="font-medium text-blue-800 text-sm sm:text-base">Upload Details</h3>
              <div className="mt-2 text-xs sm:text-sm">
                <p><span className="font-medium">Year:</span> {year}</p>
                <p><span className="font-medium">Course:</span> {courses.find(c => c.id == selectedCourse)?.name || 'Unknown Course'}</p>
                <p><span className="font-medium">File:</span> {file?.name || 'No file selected'}</p>
                <p><span className="font-medium">Questions:</span> {parsedQuestions.length}</p>
              </div>
            </div>
            {renderQuestionEditor()}
          </form>
        )}
        
        {message.text && (
          <div
            className={`mt-4 sm:mt-6 rounded-lg p-3 sm:p-4 text-xs sm:text-base ${
              message.type === 'error'
                ? 'bg-red-100 text-red-700'
                : message.type === 'success'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-blue-100 text-blue-700'
            }`}
          >
            {message.text}
          </div>
        )}

        {uploadStatus && step === 1 && (
          <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-medium text-gray-800 mb-2 text-xs sm:text-base">Upload Details</h3>
            <ul className="space-y-1 text-xs sm:text-sm text-gray-600">
              <li>
                <span className="font-medium">Year:</span> {uploadStatus.year}
              </li>
              <li>
                <span className="font-medium">Course:</span> {uploadStatus.course}
              </li>
              <li>
                <span className="font-medium">File:</span> {uploadStatus.filename}
              </li>
              <li>
                <span className="font-medium">Questions:</span> {uploadStatus.count}
              </li>
              <li>
                <span className="font-medium">Status:</span> <span className="text-yellow-600">Pending Admin Approval</span>
              </li>
            </ul>
            <p className="mt-2 sm:mt-3 text-xs sm:text-sm text-gray-500">
              You can track the approval status in your dashboard.
            </p>
          </div>
        )}
      </div>

      {step === 1 && (
        <div className="mt-6 sm:mt-8 bg-blue-50 p-3 sm:p-4 rounded-lg">
          <h3 className="font-medium text-blue-800 mb-2 text-xs sm:text-base">How to format your file</h3>
          <p className="text-xs sm:text-sm text-blue-700 mb-2">
            For best results, structure your questions like this:
          </p>
          <pre className="bg-white p-2 sm:p-3 rounded text-xs sm:text-sm overflow-x-auto">
{`1. What is 2+2?
a) 3
b) 4
c) 5
d) 6
Answer: b

2. Capital of France?
a) London
b) Berlin
c) Paris
d) Madrid
Answer: c

3. Newton's first law is also known as:
(a) Law of inertia
(b) Law of acceleration
(c) Law of action-reaction
(d) Law of gravitation
Ans: a`}
          </pre>
          <p className="mt-2 text-xs sm:text-sm text-blue-700">
            The parser supports various formats including:
          </p>
          <ul className="text-xs sm:text-sm text-blue-700 list-disc pl-5 mt-1">
            <li>Different numbering styles: 1), 1., (1)</li>
            <li>Option formats: a), a., (a)</li>
            <li>Answer indicators: Answer, Ans, Correct, Corr</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default UploadPassQuestions;