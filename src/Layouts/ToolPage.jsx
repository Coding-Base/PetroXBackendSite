// src/pages/ToolsPage.jsx
import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import { motion } from 'framer-motion';
import { X, Plus, ArrowLeft } from 'lucide-react';

export default function ToolsPage({ onBack }) {
  const [showGame, setShowGame] = useState(false);
  const [showCalculator, setShowCalculator] = useState(false);
  const [courses, setCourses] = useState([{ name: '', units: '', grade: 'A' }]);
  const [gpa, setGpa] = useState(null);
  
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.4,
        ease: "easeOut"
      }
    },
    hover: {
      scale: 1.03,
      boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
      transition: { duration: 0.3 }
    }
  };

  const gradePoints = {
    'A': 5,
    'B': 4,
    'C': 3,
    'D': 2,
    'E': 1,
    'F': 0
  };

  const addCourse = () => {
    setCourses([...courses, { name: '', units: '', grade: 'A' }]);
  };

  const removeCourse = (index) => {
    if (courses.length <= 1) return;
    const newCourses = [...courses];
    newCourses.splice(index, 1);
    setCourses(newCourses);
  };

  const handleCourseChange = (index, field, value) => {
    const newCourses = [...courses];
    newCourses[index][field] = value;
    setCourses(newCourses);
    setGpa(null); // Reset GPA when fields change
  };

  const calculateGPA = () => {
    let totalPoints = 0;
    let totalUnits = 0;
    let valid = true;

    courses.forEach(course => {
      const units = parseFloat(course.units);
      if (isNaN(units)) {
        valid = false;
        return;
      }
      totalPoints += gradePoints[course.grade] * units;
      totalUnits += units;
    });

    if (!valid || totalUnits === 0) {
      alert('Please enter valid units for all courses');
      return;
    }

    setGpa(totalPoints / totalUnits);
  };

  const resetCalculator = () => {
    setCourses([{ name: '', units: '', grade: 'A' }]);
    setGpa(null);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold text-gray-800">Utilities Collection</h2>
        <Button 
          onClick={onBack}
          className="bg-gray-100 text-gray-800 hover:bg-gray-200 flex items-center"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Dashboard
        </Button>
      </div>
      
      {showGame ? (
        <div className="flex flex-col h-full">
          <div className="flex justify-between items-center bg-gradient-to-r from-purple-600 to-indigo-600 p-4 rounded-t-xl">
            <h3 className="text-white font-bold">Word Game Battle</h3>
            <Button 
              className="bg-white/20 hover:bg-white/30 text-white"
              onClick={() => setShowGame(false)}
            >
              Close Game
            </Button>
          </div>
          <div className="overflow-auto" style={{ height: 'calc(100vh - 200px)' }}>
            <iframe
              src="https://wordgame-70j8.onrender.com/"
              title="Word Game"
              className="w-full h-full min-h-[500px] border-0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      ) : showCalculator ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-6"
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-blue-700">GPA CALCULATOR</h3>
            <Button 
              className="bg-gray-100 text-gray-800 hover:bg-gray-200"
              onClick={() => setShowCalculator(false)}
            >
              <X className="h-4 w-4 mr-2" /> Close
            </Button>
          </div>
          
          <div className="mb-6">
            <div className="grid grid-cols-12 gap-4 mb-3 font-medium text-gray-700 text-sm">
              <div className="col-span-5">Course</div>
              <div className="col-span-3">Units</div>
              <div className="col-span-3">Grade</div>
              <div className="col-span-1"></div>
            </div>
            
            {/* Scrollable course list container */}
            <div className="max-h-[50vh] overflow-y-auto pr-2 mb-4 scrollbar-thin scrollbar-thumb-blue-300 scrollbar-track-blue-50 scrollbar-thumb-rounded-full">
              {courses.map((course, index) => (
                <div key={index} className="grid grid-cols-12 gap-4 mb-3">
                  <input
                    type="text"
                    placeholder="Course name"
                    value={course.name}
                    onChange={(e) => handleCourseChange(index, 'name', e.target.value)}
                    className="col-span-5 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <input
                    type="number"
                    placeholder="0"
                    value={course.units}
                    onChange={(e) => handleCourseChange(index, 'units', e.target.value)}
                    className="col-span-3 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                    step="0.5"
                  />
                  <select
                    value={course.grade}
                    onChange={(e) => handleCourseChange(index, 'grade', e.target.value)}
                    className="col-span-3 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="A">A (5 points)</option>
                    <option value="B">B (4 points)</option>
                    <option value="C">C (3 points)</option>
                    <option value="D">D (2 points)</option>
                    <option value="E">E (1 point)</option>
                    <option value="F">F (0 points)</option>
                  </select>
                  <button
                    onClick={() => removeCourse(index)}
                    disabled={courses.length <= 1}
                    className={`col-span-1 flex items-center justify-center rounded-lg ${courses.length > 1 ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
            
            <Button 
              onClick={addCourse}
              className="bg-blue-500 hover:bg-blue-600 text-white flex items-center"
            >
              <Plus className="h-4 w-4 mr-2" /> Add Course
            </Button>
          </div>
          
          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-blue-100 pt-6">
            <div className="flex items-center gap-4">
              <Button 
                onClick={calculateGPA}
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-3"
              >
                Calculate GPA
              </Button>
              <Button 
                onClick={resetCalculator}
                variant="outline"
                className="border-gray-300 text-gray-700 hover:bg-gray-100"
              >
                Reset
              </Button>
            </div>
            
            {gpa !== null && (
              <div className="text-lg font-semibold bg-white px-4 py-3 rounded-lg border border-blue-200 shadow-sm">
                Your GPA: <span className="text-blue-600">{gpa.toFixed(2)}</span>
              </div>
            )}
          </div>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* GPA Calculator Card */}
          <motion.div 
            className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-6 cursor-pointer"
            variants={cardVariants}
            initial="hidden"
            animate="visible"
            whileHover="hover"
          >
            <div className="flex items-center mb-4">
              <div className="bg-blue-100 p-3 rounded-xl mr-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-blue-700">GPA CALCULATOR</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Calculate your grade point average based on your course grades and credit hours.
            </p>
            <Button 
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => setShowCalculator(true)}
            >
              Open Calculator
            </Button>
          </motion.div>
          
          {/* Fun Game Card */}
          <motion.div 
            className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-100 rounded-2xl p-6 cursor-pointer"
            variants={cardVariants}
            initial="hidden"
            animate="visible"
            whileHover="hover"
          >
            <div className="flex items-center mb-4">
              <div className="bg-purple-100 p-3 rounded-xl mr-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-purple-700">FUN GAME</h3>
            </div>
            <p className="text-gray-600 mb-1">
              Battle of the fittest
            </p>
            <p className="text-gray-600 mb-6 text-sm">
              Challenge your peers in a knowledge battle royale!
            </p>
            <Button 
              onClick={() => setShowGame(true)}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              Play Game
            </Button>
          </motion.div>
        </div>
      )}
      
      {!showGame && !showCalculator && (
        <div className="mt-8 text-center text-gray-500">
          <p>More utilities coming soon...</p>
        </div>
      )}
    </div>
  );
}