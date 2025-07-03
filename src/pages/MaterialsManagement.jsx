// MaterialManagement.jsx
import React, { useState } from 'react';
import { useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { useGetCourses } from '@/hooks/courses';
import { useUploadMaterial } from '@/hooks/materials';

export default function MaterialsManagement() {
  const [mode, setMode] = useState('upload');
  const [materialName, setMaterialName] = useState('');
  const [tags, setTags] = useState('');
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [file, setFile] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  // const [courses, setCourses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadedMaterials, setUploadedMaterials] = useState([]);
  const [downloadedMaterials, setDownloadedMaterials] = useState([]);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const { data } = useGetCourses();
  const { mutateAsync: uploadMaterial } = useUploadMaterial();
  const courses = data?.data || [];

  useEffect(() => {
    // Load previously downloaded materials from localStorage
    const savedDownloads = JSON.parse(
      localStorage.getItem('downloadedMaterials') || '[]'
    );
    setDownloadedMaterials(savedDownloads);
  }, []);

  const handleUpload = async () => {
    if (!selectedCourseId || !materialName || !file) {
      alert('Please fill all required fields');
      return;
    }

    setIsUploading(true);

    const formData = new FormData();
    formData.append('course', selectedCourseId);
    formData.append('name', materialName);
    formData.append('tags', tags);
    formData.append('file', file);

    try {
      // const {data} = await uploadMaterial(formData);
      const response = await fetch(
        'http://127.0.0.1:8000/api/materials/upload/',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          },
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setUploadedMaterials([data, ...uploadedMaterials]);

      // Reset form
      setMaterialName('');
      setTags('');
      setFile(null);
      setSelectedCourseId('');

      alert('Material uploaded successfully');
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to upload material');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery) {
      alert('Please enter a search query');
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/materials/search/?query=${encodeURIComponent(searchQuery)}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setSearchResults(data);
      setMode('search-results');
      setShowMobileMenu(false); // Close mobile menu after search
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to search materials');
    } finally {
      setIsSearching(false);
    }
  };

  const handleDownload = async (material) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/materials/download/${material.id}/`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get download URL');
      }

      const data = await response.json();

      // Create a temporary link to trigger download
      const link = document.createElement('a');
      link.href = data.download_url;
      link.setAttribute('download', '');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Add to downloaded materials
      const newDownloaded = [material, ...downloadedMaterials];
      setDownloadedMaterials(newDownloaded);

      // Save to localStorage
      localStorage.setItem(
        'downloadedMaterials',
        JSON.stringify(newDownloaded)
      );
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download file');
    }
  };

  // File icon based on file type
  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();

    const iconClasses =
      'h-10 w-10 p-1.5 rounded-lg md:h-12 md:w-12 md:p-2 md:rounded-xl';

    if (['jpg', 'jpeg', 'png', 'gif'].includes(ext)) {
      return (
        <div className={`${iconClasses} bg-blue-100 text-blue-600`}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      );
    } else if (['pdf'].includes(ext)) {
      return (
        <div className={`${iconClasses} bg-red-100 text-red-600`}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
      );
    } else if (['doc', 'docx'].includes(ext)) {
      return (
        <div className={`${iconClasses} bg-blue-100 text-blue-600`}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
      );
    } else {
      return (
        <div className={`${iconClasses} bg-gray-100 text-gray-600`}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
      );
    }
  };

  // Get course name by ID
  const getCourseName = (courseId) => {
    const course = courses.find((c) => c.id === courseId);
    return course ? course.name : 'Unknown Course';
  };

  return (
    <div className="min-h-screen w-full bg-gray-50 p-4 sm:p-6">
      <div className="mx-auto max-w-7xl">
        {/* Mobile menu button */}
        <div className="mb-4 flex items-center justify-between md:hidden">
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="rounded-lg bg-indigo-600 p-2 text-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <h1 className="text-xl font-bold text-indigo-900">Study Materials</h1>
          <div className="w-10"></div> {/* Spacer for alignment */}
        </div>

        <div className="mb-6 flex flex-col items-center justify-between gap-4 md:mb-8 md:flex-row">
          <div className="hidden md:block">
            <h1 className="text-2xl font-bold text-indigo-900 md:text-3xl">
              Study Materials
            </h1>
            <p className="hidden text-indigo-600 md:block">
              Upload, search, and access learning resources
            </p>
          </div>

          <div className="flex w-full flex-col items-center gap-3 md:flex-row md:gap-4">
            <div className="relative w-full">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-indigo-200 bg-white py-2 pr-4 pl-10 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 md:rounded-xl md:py-3"
                placeholder="Search materials..."
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <svg
                className="absolute top-2.5 left-3 h-4 w-4 text-indigo-400 md:top-3.5 md:h-5 md:w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>

            <Button
              onClick={handleSearch}
              variant="primary"
              disabled={isSearching}
            >
              {isSearching ? (
                <>
                  <svg
                    className="mr-2 h-4 w-4 animate-spin text-white md:h-5 md:w-5"
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
                  Searching...
                </>
              ) : (
                'Search'
              )}
            </Button>
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {showMobileMenu && (
          <div className="mb-6 rounded-xl bg-white p-4 shadow-lg md:hidden">
            <button
              onClick={() => {
                setMode('upload');
                setShowMobileMenu(false);
              }}
              className={`mb-2 w-full rounded-lg px-4 py-3 text-center font-medium ${
                mode === 'upload'
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                  : 'bg-white text-indigo-700 shadow hover:bg-indigo-50'
              }`}
            >
              Upload Material
            </button>
            <button
              onClick={() => {
                setMode('download');
                setShowMobileMenu(false);
              }}
              className={`mb-2 w-full rounded-lg px-4 py-3 text-center font-medium ${
                mode === 'download'
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                  : 'bg-white text-indigo-700 shadow hover:bg-indigo-50'
              }`}
            >
              My Materials
            </button>
            <button
              onClick={() => {
                setMode('search-results');
                setShowMobileMenu(false);
              }}
              className={`w-full rounded-lg px-4 py-3 text-center font-medium ${
                mode === 'search-results'
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                  : 'bg-white text-indigo-700 shadow hover:bg-indigo-50'
              }`}
            >
              Search Results
            </button>
          </div>
        )}

        {/* Desktop mode buttons */}
        <div className="mb-6 hidden space-x-2 md:mb-8 md:flex md:space-x-4">
          <button
            onClick={() => setMode('upload')}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-all md:rounded-xl md:px-6 md:py-3 md:text-base ${
              mode === 'upload'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                : 'bg-white text-indigo-700 shadow hover:bg-indigo-50'
            }`}
          >
            Upload Material
          </button>
          <button
            onClick={() => setMode('download')}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-all md:rounded-xl md:px-6 md:py-3 md:text-base ${
              mode === 'download'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                : 'bg-white text-indigo-700 shadow hover:bg-indigo-50'
            }`}
          >
            My Materials
          </button>
          <button
            onClick={() => setMode('search-results')}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-all md:rounded-xl md:px-6 md:py-3 md:text-base ${
              mode === 'search-results'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                : 'bg-white text-indigo-700 shadow hover:bg-indigo-50'
            }`}
          >
            Search Results
          </button>
        </div>

        {mode === 'upload' && (
          <div className="mb-6 rounded-xl border border-indigo-100 bg-white p-5 shadow-lg md:mb-8 md:rounded-2xl md:p-8 md:shadow-xl">
            <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-indigo-800 md:mb-6 md:text-2xl">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 md:h-6 md:w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              Upload New Material
            </h2>

            <div className="mb-4 grid grid-cols-1 gap-4 md:mb-6 md:gap-6">
              <div>
                <label className="mb-1 block text-sm font-medium text-indigo-700 md:mb-2">
                  Course
                </label>
                <select
                  value={selectedCourseId}
                  onChange={(e) => setSelectedCourseId(e.target.value)}
                  className="w-full rounded-lg border border-indigo-200 bg-white px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 md:rounded-xl md:px-4 md:py-3"
                >
                  <option value="">Select a course</option>
                  {courses?.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-indigo-700 md:mb-2">
                  Material Name
                </label>
                <input
                  type="text"
                  value={materialName}
                  onChange={(e) => setMaterialName(e.target.value)}
                  className="w-full rounded-lg border border-indigo-200 bg-white px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 md:rounded-xl md:px-4 md:py-3"
                  placeholder="Enter material name"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-indigo-700 md:mb-2">
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full rounded-lg border border-indigo-200 bg-white px-3 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 md:rounded-xl md:px-4 md:py-3"
                  placeholder="e.g., math, calculus, formulas"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-indigo-700 md:mb-2">
                  File
                </label>
                <div className="flex w-full items-center justify-center">
                  <label className="flex h-32 w-full cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-indigo-300 bg-indigo-50 transition-colors hover:bg-indigo-100 md:rounded-2xl">
                    <div className="flex flex-col items-center justify-center p-4">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="mb-2 h-8 w-8 text-indigo-500 md:h-10 md:w-10"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                      <p className="text-center text-xs font-medium text-indigo-600 md:text-sm">
                        {file ? file.name : 'Click to upload or drag and drop'}
                      </p>
                      <p className="mt-1 text-xs text-indigo-400">
                        Max file size: 10MB
                      </p>
                    </div>
                    <input
                      type="file"
                      className="hidden"
                      onChange={(e) => setFile(e.target.files[0])}
                    />
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="flex w-full items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-sm text-white shadow-lg transition-all hover:from-indigo-700 hover:to-purple-700 hover:shadow-xl disabled:opacity-70 md:w-auto md:rounded-xl md:px-8 md:py-3 md:text-base"
              >
                {isUploading ? (
                  <>
                    <svg
                      className="mr-2 h-4 w-4 animate-spin text-white md:h-5 md:w-5"
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
                    Uploading...
                  </>
                ) : (
                  <>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="mr-1 h-4 w-4 md:mr-2 md:h-5 md:w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    Upload Material
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {(mode === 'download' || mode === 'search-results') && (
          <div className="rounded-xl border border-indigo-100 bg-white p-4 shadow-lg md:rounded-2xl md:p-6 md:shadow-xl">
            <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-indigo-800 md:mb-6 md:text-2xl">
              {mode === 'search-results' ? (
                <>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 md:h-6 md:w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                  Search Results
                </>
              ) : (
                <>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 md:h-6 md:w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"
                    />
                  </svg>
                  My Materials
                </>
              )}
            </h2>

            {mode === 'download' && downloadedMaterials.length === 0 && (
              <div className="rounded-lg border-2 border-dashed border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50 py-8 text-center md:rounded-2xl md:py-16">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="mx-auto mb-3 h-16 w-16 text-indigo-300 md:mb-4 md:h-24 md:w-24"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h3 className="mb-2 text-lg font-medium text-indigo-700 md:text-xl">
                  No materials yet
                </h3>
                <p className="mb-4 text-sm text-indigo-500 md:text-base">
                  Download materials to see them here
                </p>
                <button
                  onClick={() => setMode('search-results')}
                  className="rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-sm text-white shadow-lg transition-all hover:from-indigo-700 hover:to-purple-700 hover:shadow-xl md:rounded-xl md:px-6 md:py-3 md:text-base"
                >
                  Search Materials
                </button>
              </div>
            )}

            {(mode === 'search-results' || downloadedMaterials.length > 0) && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 md:gap-6 lg:grid-cols-4">
                {(mode === 'search-results'
                  ? searchResults
                  : downloadedMaterials
                ).map((material) => (
                  <div
                    key={material.id}
                    className="flex flex-col overflow-hidden rounded-lg border border-indigo-100 bg-white transition-all hover:shadow-md md:rounded-2xl md:hover:shadow-lg"
                  >
                    <div className="flex justify-center bg-gradient-to-r from-indigo-50 to-purple-50 p-3 md:p-4">
                      {getFileIcon(material.name)}
                    </div>
                    <div className="flex-grow p-3 md:p-4">
                      <h4
                        className="mb-1 truncate text-sm font-bold text-gray-800 md:text-base"
                        title={material.name}
                      >
                        {material.name}
                      </h4>
                      <div className="mb-2 flex items-start gap-2 text-xs text-indigo-600 md:text-sm">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="mt-0.5 h-3 w-3 md:h-4 md:w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                          />
                        </svg>
                        <span className="truncate">
                          {getCourseName(material.course)}
                        </span>
                      </div>
                      {material.tags && (
                        <div className="mb-2 flex flex-wrap gap-1 md:mb-3">
                          {material.tags.split(',').map((tag, index) => (
                            <span
                              key={index}
                              className="rounded-full bg-indigo-100 px-1.5 py-0.5 text-[10px] text-indigo-700 md:px-2 md:py-1 md:text-xs"
                            >
                              {tag.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                      <p className="mt-1 flex items-center text-[10px] text-gray-500 md:mt-2 md:text-xs">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="mr-1 h-2.5 w-2.5 md:h-3 md:w-3"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {new Date(material.uploaded_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="px-3 pb-3 md:px-4 md:pb-4">
                      <button
                        onClick={() => handleDownload(material)}
                        className="flex w-full items-center justify-center rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 px-3 py-1.5 text-sm text-white shadow-md transition-all hover:from-emerald-600 hover:to-teal-600 hover:shadow-lg md:px-4 md:py-2 md:text-base"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="mr-1 h-4 w-4 md:mr-2 md:h-5 md:w-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                          />
                        </svg>
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
