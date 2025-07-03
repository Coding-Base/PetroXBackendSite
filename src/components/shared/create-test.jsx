// CreateGroupTest.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../ui/button';
import { useGetCourses } from '@/hooks/courses';
import { useCreateTest } from '@/hooks/tests';

export default function CreateTest() {
  const navigate = useNavigate();
  // const [courses, setCourses] = useState([]);
  const [name, setName] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [questionCount, setQuestionCount] = useState(5);
  const [duration, setDuration] = useState(10); // in minutes
  const [invitees, setInvitees] = useState(['']); // array of emails
  const [scheduledStart, setScheduledStart] = useState(''); // local datetime‐local string
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [testType, setTestType] = useState('personal'); // 'personal' or 'group'

  const { isLoading, data } = useGetCourses();
  const { isLoading: isSubmitting, mutateAsync: createTestAsync } =
    useCreateTest();
  const courses = data?.data ?? [];

  const handleInviteeChange = (index, value) => {
    const newInvitees = [...invitees];
    newInvitees[index] = value;
    setInvitees(newInvitees);
  };

  const addInviteeField = () => {
    setInvitees([...invitees, '']);
  };

  const removeInviteeField = (index) => {
    const newInvitees = invitees.filter((_, idx) => idx !== index);
    setInvitees(newInvitees.length ? newInvitees : ['']);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    // Basic validation
    if (!name || !selectedCourse || !scheduledStart) {
      setError('Name, course, and scheduled start date/time are required.');
      return;
    }

    // Validate group test has at least one valid email
    if (testType === 'group') {
      const validEmails = invitees.filter((email) => email.trim() !== '');
      if (validEmails.length === 0) {
        setError('Please add at least one email for group test.');
        return;
      }
    }

    try {
      // Convert to UTC ISO string
      const scheduledStartUtc = new Date(scheduledStart).toISOString();

      const payload = {
        name,
        course: selectedCourse,
        question_count: questionCount,
        duration_minutes: duration,
        // Only include invitees for group tests
        invitees:
          testType === 'group'
            ? invitees.filter((email) => email.trim() !== '')
            : [],
        scheduled_start: scheduledStartUtc
      };

      const { data } = await createTestAsync(payload);

      // Show success message, then redirect
      setSuccessMsg(
        testType === 'personal'
          ? 'Personal test created successfully! Redirecting...'
          : 'Group test created successfully! Redirecting...'
      );

      setTimeout(() => {
        navigate(`/dashboard/group-test/${data.id}`);
      }, 1000);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.error ||
          `Failed to create ${testType} test. Please try again.`
      );
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-md p-6 text-center">
        <p>Loading courses…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-6 max-h-screen overflow-y-auto md:max-h-none md:overflow-visible">
      <h2 className="mb-6 text-center text-2xl font-bold">Create Test</h2>

      {error && (
        <div className="mb-4 rounded bg-red-100 p-3 text-red-700">{error}</div>
      )}
      {successMsg && (
        <div className="mb-4 rounded bg-green-100 p-3 text-green-700">
          {successMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Test Type Selection */}
        <div className="rounded-lg bg-gray-50 p-4">
          <label className="mb-2 block text-sm font-medium">Test Type</label>
          <div className="flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-6">
            <label className="flex items-center">
              <input
                type="radio"
                name="testType"
                value="personal"
                checked={testType === 'personal'}
                onChange={() => setTestType('personal')}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500"
                disabled={isSubmitting}
              />
              <span className="text-gray-700">Personal Test (for myself)</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="testType"
                value="group"
                checked={testType === 'group'}
                onChange={() => setTestType('group')}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500"
                disabled={isSubmitting}
              />
              <span className="text-gray-700">Group Test (invite friends)</span>
            </label>
          </div>
        </div>

        {/* Test Name */}
        <div>
          <label className="mb-2 block text-sm font-medium">Test Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            required
            disabled={isSubmitting}
            placeholder="Enter test name"
          />
        </div>

        {/* Course Selection */}
        <div>
          <label className="mb-2 block text-sm font-medium">Course</label>
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            required
            disabled={isSubmitting}
          >
            <option value="">Select a course</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))}
          </select>
        </div>

        {/* Question Count & Duration */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium">
              Number of Questions
            </label>
            <input
              type="number"
              min="1"
              value={questionCount}
              onChange={(e) => setQuestionCount(+e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              required
              disabled={isSubmitting}
            />
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium">
              Duration (minutes)
            </label>
            <input
              type="number"
              min="1"
              value={duration}
              onChange={(e) => setDuration(+e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              required
              disabled={isSubmitting}
            />
          </div>
        </div>

        {/* Scheduled Start Date & Time */}
        <div>
          <label className="mb-2 block text-sm font-medium">
            Scheduled Start (Date & Time)
          </label>
          <input
            type="datetime-local"
            value={scheduledStart}
            onChange={(e) => setScheduledStart(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            required
            disabled={isSubmitting}
          />
        </div>

        {/* Conditionally render invitees section only for group test */}
        {testType === 'group' && (
          <div className="rounded-lg bg-blue-50 p-4">
            <label className="mb-2 block text-sm font-medium">
              Invitee Emails (optional)
            </label>
            <p className="mb-3 text-sm text-gray-600">
              Add email addresses of friends you want to invite to this test
            </p>

            {invitees.map((email, idx) => (
              <div key={idx} className="mb-2 flex items-center space-x-2">
                <input
                  type="email"
                  placeholder="friend@example.com"
                  value={email}
                  onChange={(e) => handleInviteeChange(idx, e.target.value)}
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
                {invitees.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeInviteeField(idx)}
                    className="p-2 text-red-600 hover:text-red-800 disabled:text-gray-400"
                    title="Remove email"
                    disabled={isSubmitting}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={addInviteeField}
              className="mt-2 flex items-center text-blue-600 hover:text-blue-800 disabled:text-gray-400"
              disabled={isSubmitting}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="mr-1 h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
                  clipRule="evenodd"
                />
              </svg>
              Add another email
            </button>
          </div>
        )}

        {/* Submit Button */}
        <div>
          <Button
            type="submit"
            className="flex w-full items-center justify-center rounded-lg bg-blue-600 py-3 text-white transition hover:bg-blue-700 disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <svg
                  className="mr-3 -ml-1 h-5 w-5 animate-spin text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Creating...
              </>
            ) : (
              `Create ${testType === 'personal' ? 'Personal' : 'Group'} Test`
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}