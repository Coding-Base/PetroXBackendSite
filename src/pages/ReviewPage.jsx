// ReviewPage.jsx
import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import axios from 'axios';

const ReviewPage = ({ sessionId, isOpen, onClose, onRetake }) => {
  const [testDetails, setTestDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch test results when modal opens
  useEffect(() => {
    if (!isOpen || !sessionId) return;

    const fetchResults = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('access_token');
        const response = await axios.get(
          `https://petroxtestbackend.onrender.com/api/test-session/${sessionId}/`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        setTestDetails(response.data);
        setError('');
      } catch (err) {
        console.error('Failed to fetch test results', err);
        setError('Failed to load test results. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [sessionId, isOpen]);

  const questions = testDetails?.questions || [];
  const score = testDetails?.score || 0;
  const totalQuestions = testDetails?.question_count || questions.length;

  // Find option text by key
  const getOptionText = (question, optionKey) => {
    if (!optionKey) return 'Not answered';
    const key = optionKey.toUpperCase();
    const field = `option_${key.toLowerCase()}`;
    return question[field] || `Option ${key}`;
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="bg-opacity-75 fixed inset-0 bg-black" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="h3"
                  className="border-b pb-4 text-2xl leading-6 font-bold text-gray-900"
                >
                  Test Review
                  <p className="mt-1 text-sm font-normal text-gray-500">
                    Reviewing all questions
                  </p>
                </Dialog.Title>

                {loading ? (
                  <div className="py-12 text-center">
                    <div className="flex justify-center">
                      <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-500"></div>
                    </div>
                    <p className="mt-4 text-gray-600">
                      Loading your test results...
                    </p>
                  </div>
                ) : error ? (
                  <div className="py-8 text-center">
                    <div className="mb-4 text-red-500">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="mx-auto h-12 w-12"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </div>
                    <p className="font-medium text-red-600">{error}</p>
                    <button
                      onClick={onClose}
                      className="mt-4 rounded-md bg-gray-100 px-4 py-2 hover:bg-gray-200"
                    >
                      Close
                    </button>
                  </div>
                ) : (
                  <div className="mt-6">
                    <div className="mb-6 flex items-center justify-between">
                      <div className="rounded-lg bg-blue-50 px-4 py-2">
                        <span className="font-medium text-blue-800">
                          {score} / {totalQuestions}
                        </span>{' '}
                        questions correct
                      </div>

                      <div className="rounded-lg bg-red-50 px-4 py-2">
                        <span className="font-medium text-red-800">
                          {totalQuestions - score}
                        </span>{' '}
                        questions incorrect
                      </div>
                    </div>

                    <div className="max-h-[60vh] space-y-8 overflow-y-auto py-2 pr-2">
                      {questions.map((question, index) => {
                        const correctOption = question.correct_option;
                        return (
                          <div
                            key={question.id}
                            className="rounded-xl border border-gray-200 p-5 transition-colors hover:border-blue-200"
                          >
                            <div className="flex items-start">
                              <div
                                className={`${
                                  correctOption
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                } mr-3 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full font-bold`}
                              >
                                {index + 1}
                              </div>
                              <div className="flex-1">
                                <h4 className="font-medium text-gray-800">
                                  {question.question_text}
                                </h4>

                                <div className="mt-4">
                                  <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                                    <div className="mb-2 flex items-center">
                                      <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-white">
                                        ✓
                                      </span>
                                      <h5 className="font-medium text-green-800">
                                        Correct Answer
                                      </h5>
                                    </div>
                                    <p className="ml-8">
                                      <span className="font-bold">
                                        {correctOption}:
                                      </span>
                                      {getOptionText(question, correctOption)}
                                    </p>
                                  </div>

                                  {/* Explanation section */}
                                  {question.explanation && (
                                    <div className="mt-4 rounded-lg bg-blue-50 p-4">
                                      <h5 className="mb-2 font-medium text-blue-800">
                                        Explanation
                                      </h5>
                                      <p className="text-gray-700">
                                        {question.explanation}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="mt-8 flex justify-end space-x-3 border-t pt-4">
                      <button
                        type="button"
                        className="rounded-lg bg-gray-100 px-6 py-3 transition-colors hover:bg-gray-200"
                        onClick={onClose}
                      >
                        Close Review
                      </button>
                      <button
                        type="button"
                        className="rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700"
                        onClick={() => {
                          onClose();
                          onRetake(); // Call the retake function
                        }}
                      >
                        Retake Test
                      </button>
                    </div>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default ReviewPage;
