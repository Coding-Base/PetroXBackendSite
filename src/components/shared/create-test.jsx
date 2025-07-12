// src/components/CreateTest.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { fetchCourses, createGroupTest } from '@/api/index';

export default function CreateTest() {
  const navigate = useNavigate();

  // Form state
  const [name, setName] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [questionCount, setQuestionCount] = useState(5);
  const [duration, setDuration] = useState(10); // minutes
  const [invitees, setInvitees] = useState(['']);
  const [scheduledStart, setScheduledStart] = useState('');
  const [testType, setTestType] = useState('personal');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Course fetching state
  const [courses, setCourses] = useState([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(true);
  const [courseError, setCourseError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch courses on mount
  useEffect(() => {
    const loadCourses = async () => {
      try {
        const response = await fetchCourses();
        // If your API returns { data: [...] }
        const courseArr = Array.isArray(response.data) ? response.data : response;
        setCourses(courseArr);
      } catch (err) {
        console.error('Failed to fetch courses:', err);
        setCourseError('Failed to load courses. Please try again later.');
      } finally {
        setIsLoadingCourses(false);
      }
    };
    loadCourses();
  }, []);

  const handleInviteeChange = (idx, val) => {
    const newInvitees = [...invitees];
    newInvitees[idx] = val;
    setInvitees(newInvitees);
  };

  const addInvitee = () => setInvitees([...invitees, '']);
  const removeInvitee = (idx) => {
    if (invitees.length <= 1) return;
    setInvitees(invitees.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    // Validation
    if (!name.trim() || !selectedCourse || !scheduledStart) {
      setError('Name, course, and scheduled start are required.');
      return;
    }
    if (questionCount < 1 || duration < 1) {
      setError('Question count and duration must be at least 1');
      return;
    }
    if (
      testType === 'group' &&
      invitees.filter((em) => em.trim() !== '').length === 0
    ) {
      setError('Please add at least one valid email for a group test.');
      return;
    }

    try {
      setIsSubmitting(true);

      // Format date to UTC without changing time value
      const scheduledDate = new Date(scheduledStart);
      const utcDate = new Date(
        Date.UTC(
          scheduledDate.getFullYear(),
          scheduledDate.getMonth(),
          scheduledDate.getDate(),
          scheduledDate.getHours(),
          scheduledDate.getMinutes()
        )
      );

      const payload = {
        name: name.trim(),
        course: selectedCourse,
        question_count: Number(questionCount),
        duration_minutes: Number(duration),
        scheduled_start: new Date(scheduledStart).toISOString(),
        invitees: testType === 'group'
          ? invitees.map(email => email.trim()).filter(email => email !== '')
          : [],
      };

      const response = await createGroupTest(payload);
      const testId = response.id || response.data?.id;

      setSuccessMsg(
        `${testType === 'personal' ? 'Personal' : 'Group'} test created! Redirecting...`
      );

      setTimeout(() => {
        navigate(`/dashboard/group-test/${testId}`);
      }, 1500);
    } catch (err) {
      console.error('Test creation failed:', err);
      setError(
        err.response?.data?.error?.message ||
        err.message ||
        `Failed to create ${testType} test. Please try again.`
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoadingCourses) {
    return (
      <div className="mx-auto max-w-md p-6 text-center">
        <p>Loading courses...</p>
      </div>
    );
  }

  if (courseError) {
    return (
      <div className="mx-auto max-w-md p-6 text-center text-red-500">
        <p>{courseError}</p>
        <Button
          onClick={() => window.location.reload()}
          className="mt-4"
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
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
        {/* Test Type */}
        <div className="space-x-4">
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="testType"
              value="personal"
              checked={testType === 'personal'}
              onChange={() => setTestType('personal')}
              disabled={isSubmitting}
              className="mr-2"
            />
            Personal
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              name="testType"
              value="group"
              checked={testType === 'group'}
              onChange={() => setTestType('group')}
              disabled={isSubmitting}
              className="mr-2"
            />
            Group
          </label>
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium mb-1">Test Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isSubmitting}
            className="w-full rounded-lg border px-4 py-2 focus:ring-blue-500"
            placeholder="Enter test name"
            required
          />
        </div>

        {/* Course */}
        <div>
          <label className="block text-sm font-medium mb-1">Course</label>
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            disabled={isSubmitting || courses.length === 0}
            className="w-full rounded-lg border px-4 py-2 focus:ring-blue-500"
            required
          >
            <option value="">Select a course</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          {courses.length === 0 && (
            <p className="text-red-500 text-sm mt-1">No courses available</p>
          )}
        </div>

        {/* Count & Duration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Questions (1-100)
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={questionCount}
              onChange={(e) => {
                const val = Math.min(100, Math.max(1, Number(e.target.value) || 1));
                setQuestionCount(val);
              }}
              disabled={isSubmitting}
              className="w-full rounded-lg border px-4 py-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Duration (minutes, 1-180)
            </label>
            <input
              type="number"
              min="1"
              max="180"
              value={duration}
              onChange={(e) => {
                const val = Math.min(180, Math.max(1, Number(e.target.value) || 1));
                setDuration(val);
              }}
              disabled={isSubmitting}
              className="w-full rounded-lg border px-4 py-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        {/* Scheduled Start */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Scheduled Start
          </label>
          <input
            type="datetime-local"
            value={scheduledStart}
            onChange={(e) => setScheduledStart(e.target.value)}
            disabled={isSubmitting}
            className="w-full rounded-lg border px-4 py-2 focus:ring-blue-500"
            required
            min={new Date().toISOString().slice(0, 16)}
          />
        </div>

        {/* Invitees */}
        {testType === 'group' && (
          <div>
            <label className="block text-sm font-medium mb-1">
              Invitee Emails
            </label>
            {invitees.map((em, idx) => (
              <div key={idx} className="flex items-center mb-2 space-x-2">
                <input
                  type="email"
                  placeholder="friend@example.com"
                  value={em}
                  onChange={(e) => handleInviteeChange(idx, e.target.value)}
                  disabled={isSubmitting}
                  className="flex-1 rounded-lg border px-3 py-2 focus:ring-blue-500"
                  required={idx === 0}
                />
                {invitees.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeInvitee(idx)}
                    disabled={isSubmitting}
                    className="px-3 py-2 text-red-600 hover:text-red-800 disabled:opacity-50"
                    aria-label="Remove invitee"
                  >
                    &times;
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={addInvitee}
              disabled={isSubmitting || invitees.length >= 10}
              className="text-blue-600 hover:text-blue-800 disabled:opacity-50"
            >
              + Add another email
            </button>
            {invitees.length >= 10 && (
              <p className="text-sm text-gray-500 mt-1">Maximum 10 invitees</p>
            )}
          </div>
        )}

        {/* Submit */}
        <div>
          <Button
            type="submit"
            disabled={isSubmitting || courses.length === 0}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg disabled:opacity-50 transition-colors"
          >
            {isSubmitting
              ? 'Creating...'
              : `Create ${testType === 'personal' ? 'Personal' : 'Group'} Test`}
          </Button>
        </div>
      </form>
    </div>
  );
}