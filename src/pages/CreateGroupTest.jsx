// src/components/CreateGroupTest.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCourses, api } from '@/api/index';
import { Button } from '../components/ui/button';

export default function CreateGroupTest() {
  const navigate = useNavigate();

  // form fields
  const [name, setName] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [questionCount, setQuestionCount] = useState(5);
  const [duration, setDuration] = useState(10);
  const [invitees, setInvitees] = useState(['']);
  const [scheduledStart, setScheduledStart] = useState('');

  // UI state
  const [courses, setCourses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchCourses()
      .then(res => setCourses(res.data))
      .catch(err => {
        console.error('Failed to load courses', err);
        setError('Could not load courses.');
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handleInviteeChange = (idx, email) => {
    const copy = [...invitees];
    copy[idx] = email;
    setInvitees(copy);
  };

  const addInviteeField = () => {
    setInvitees([...invitees, '']);
  };

  const removeInviteeField = idx => {
    const copy = invitees.filter((_, i) => i !== idx);
    setInvitees(copy.length ? copy : ['']);
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setIsSubmitting(true);

    if (!name || !selectedCourse || !scheduledStart) {
      setError('Name, course, and scheduled start date/time are required.');
      setIsSubmitting(false);
      return;
    }

    try {
      const payload = {
        name,
        course: selectedCourse,
        question_count: questionCount,
        duration_minutes: duration,
        invitees: invitees.filter(email => email.trim() !== ''),
        scheduled_start: new Date(scheduledStart).toISOString(),
      };

      const { data } = await api.post('/api/create-group-test/', payload);
      setSuccessMsg('Group test created successfully! Redirecting…');
      setTimeout(() => navigate(`/dashboard/group-test/${data.id}`), 1000);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.error ||
          'Failed to create group test. Please try again.'
      );
      setIsSubmitting(false);
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
    <div className="mx-auto max-w-2xl rounded-xl bg-white p-6 shadow-md">
      <h2 className="mb-4 text-center text-2xl font-bold">
        Create Group Test
      </h2>

      {error && (
        <div className="mb-4 rounded bg-red-100 p-3 text-red-700">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="mb-4 rounded bg-green-100 p-3 text-green-700">
          {successMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Test Name */}
        <div>
          <label className="mb-1 block text-sm font-medium">Test Name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            required
            disabled={isSubmitting}
          />
        </div>

        {/* Course */}
        <div>
          <label className="mb-1 block text-sm font-medium">Course</label>
          <select
            value={selectedCourse}
            onChange={e => setSelectedCourse(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            required
            disabled={isSubmitting}
          >
            <option value="">Select a course</option>
            {courses.map(c => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Questions & Duration */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">
              Number of Questions
            </label>
            <input
              type="number"
              min="1"
              value={questionCount}
              onChange={e => setQuestionCount(+e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              required
              disabled={isSubmitting}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">
              Duration (minutes)
            </label>
            <input
              type="number"
              min="1"
              value={duration}
              onChange={e => setDuration(+e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              required
              disabled={isSubmitting}
            />
          </div>
        </div>

        {/* Scheduled Start */}
        <div>
          <label className="mb-1 block text-sm font-medium">
            Scheduled Start (Date & Time)
          </label>
          <input
            type="datetime-local"
            value={scheduledStart}
            onChange={e => setScheduledStart(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            required
            disabled={isSubmitting}
          />
        </div>

        {/* Invitee Emails */}
        <div>
          <label className="mb-1 block text-sm font-medium">
            Invitee Emails
          </label>
          {invitees.map((email, idx) => (
            <div key={idx} className="mb-2 flex items-center space-x-2">
              <input
                type="email"
                placeholder="invitee@example.com"
                value={email}
                onChange={e => handleInviteeChange(idx, e.target.value)}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
                disabled={isSubmitting}
              />
              <Button
                type="button"
                onClick={() => removeInviteeField(idx)}
                className="text-red-600 hover:text-red-800"
                disabled={isSubmitting}
              >
                &times;
              </Button>
            </div>
          ))}
          <Button
            type="button"
            onClick={addInviteeField}
            className="mt-2 text-blue-600 hover:text-blue-800"
            disabled={isSubmitting}
          >
            + Add another email
          </Button>
        </div>

        {/* Submit */}
        <div>
          <Button
            type="submit"
            className="w-full rounded-lg bg-blue-600 py-3 text-white hover:bg-blue-700 disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating…' : 'Create Group Test'}
          </Button>
        </div>
      </form>
    </div>
  );
}
