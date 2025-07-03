// src/components/LandingPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  FaBook,
  FaUsers,
  FaComments,
  FaCalculator,
  FaFileUpload,
  FaGraduationCap,
  FaRobot
} from 'react-icons/fa';
import image1 from '../images/land1.png';
import image2 from '../images/land2.png';
const LandingPage = () => {
  const [loading, setLoading] = useState(true);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const observer = useRef(null);

  const slides = [
    {
      title: 'Elevate Your Academic Journey',
      subtitle: 'Access premium study materials and collaborative tools',
      image: image1
    },
    {
      title: 'Master Your Subjects',
      subtitle: 'Personalized learning with PetroMark AI assistant',
      image: image2
    },
    {
      title: 'Collaborate & Succeed',
      subtitle: 'Create group tests and study with peers',
      image: image1
    }
  ];
  // Preloader effect
  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  // Carousel effect
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [slides.length]);

  // Scroll detection for header
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Intersection observer for animations
  useEffect(() => {
    observer.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
          }
        });
      },
      { threshold: 0.1 }
    );

    const sections = document.querySelectorAll('.animate-section');
    sections.forEach((section) => observer.current.observe(section));

    return () => {
      if (observer.current) {
        observer.current.disconnect();
      }
    };
  }, []);

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="relative mx-auto mb-6 h-20 w-20">
            <div className="absolute inset-0 animate-spin rounded-full border-4 border-gray-700 border-t-indigo-500"></div>
          </div>
          <h1 className="text-4xl font-bold tracking-wider text-white">
            <span className="text-indigo-400">PETRO</span>
            <span className="text-amber-400">X</span>
          </h1>
          <p className="mt-4 font-light text-gray-400">
            Preparing your learning experience
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="relative h-[90vh] overflow-hidden">
        {/* Carousel */}
        <div className="absolute inset-0 transition-opacity duration-1000 ease-in-out">
          {slides.map((slide, index) => (
            <div
              key={index}
              className={`absolute inset-0 transition-opacity duration-1000 ${
                currentSlide === index ? 'opacity-100' : 'opacity-0'
              }`}
            >
              {/* Image with 20% opacity */}
              <div
                className="absolute inset-0 bg-cover bg-center opacity-90"
                style={{ backgroundImage: `url(${slide.image})` }}
              ></div>

              {/* Dark overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
            </div>
          ))}
        </div>

        {/* Navigation */}
        <nav
          className={`fixed z-30 flex w-full items-center justify-between px-6 py-4 transition-all duration-300 md:px-12 ${
            scrolled ? 'bg-gray-900/90 backdrop-blur-sm' : 'bg-transparent'
          }`}
        >
          <div className="flex items-center">
            <h1 className="text-2xl font-bold tracking-wider text-white">
              <span className="text-indigo-400">PETRO</span>
              <span className="text-amber-400">X</span>
            </h1>
          </div>

          <div className="hidden space-x-8 md:flex">
            <a
              href="#features"
              className="text-gray-200 transition-colors hover:text-white"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="text-gray-200 transition-colors hover:text-white"
            >
              How It Works
            </a>
            <a
              href="#testimonials"
              className="text-gray-200 transition-colors hover:text-white"
            >
              Testimonials
            </a>
          </div>

          <div>
            <Link
              to="/login"
              className="rounded bg-indigo-600 px-6 py-2 font-medium text-white transition-all hover:bg-indigo-700"
            >
              Get Started
            </Link>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 flex h-full flex-col items-center justify-center px-6 text-center">
          <div className="max-w-4xl">
            <h1 className="mb-6 text-4xl leading-tight font-bold text-white md:text-5xl">
              {slides[currentSlide].title}
            </h1>
            <p className="mx-auto mb-10 max-w-2xl text-xl text-gray-200">
              {slides[currentSlide].subtitle}
            </p>
            <div className="flex flex-col justify-center gap-4 sm:flex-row">
              <Link
                to="/signup"
                className="rounded bg-indigo-600 px-8 py-3 font-medium text-white transition-all hover:bg-indigo-700"
              >
                Create Free Account
              </Link>
              <Link
                to="/features"
                className="rounded border border-gray-300 bg-transparent px-8 py-3 font-medium text-white transition-all hover:bg-white/10"
              >
                Explore Features
              </Link>
            </div>
          </div>
        </div>

        {/* Carousel Indicators */}
        <div className="absolute bottom-8 left-1/2 z-10 flex -translate-x-1/2 transform space-x-2">
          {slides.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentSlide(index)}
              className={`h-3 w-3 rounded-full transition-all ${
                currentSlide === index
                  ? 'w-6 bg-white'
                  : 'bg-white/50 hover:bg-white/80'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      </header>

      {/* Features Section */}
      <section
        style={{ marginTop: '-900px' }}
        id="features"
        className={`animate-section bg-white px-6 py-20 transition-all duration-700 md:px-12 ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
        }`}
      >
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold text-gray-800 md:text-4xl">
              Powerful Learning Tools
            </h2>
            <p className="mx-auto max-w-2xl text-gray-600">
              PetroX provides everything you need to excel academically
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <div
                key={index}
                className={`rounded-lg border border-gray-200 bg-white p-8 transition-all duration-300 hover:border-indigo-300 hover:shadow-md ${
                  isVisible ? 'opacity-100' : 'opacity-0'
                }`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div className="mb-6 text-3xl text-indigo-600">
                  {feature.icon}
                </div>
                <h3 className="mb-3 text-xl font-bold text-gray-800">
                  {feature.title}
                </h3>
                <p className="mb-4 text-gray-600">{feature.description}</p>
                <div className="flex flex-wrap gap-2">
                  {feature.tags.map((tag, tagIndex) => (
                    <span
                      key={tagIndex}
                      className="rounded bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="bg-gray-50 px-6 py-20 md:px-12">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold text-gray-800 md:text-4xl">
              How PetroX Works
            </h2>
            <p className="mx-auto max-w-2xl text-gray-600">
              A seamless learning experience designed for academic success
            </p>
          </div>

          <div className="flex flex-col items-center gap-12 lg:flex-row">
            <div className="lg:w-1/2">
              <div className="rounded-lg border border-gray-200 bg-gradient-to-br from-gray-50 to-white p-6 shadow-sm">
                <div className="flex h-80 w-full items-center justify-center rounded-lg border border-gray-300 bg-gray-100">
                  <div className="h-64 w-full rounded-xl border-2 border-dashed bg-gray-200" />
                </div>
              </div>
            </div>

            <div className="lg:w-1/2">
              <div className="space-y-8">
                {steps.map((step, index) => (
                  <div key={index} className="flex items-start">
                    <div className="mr-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
                      <span className="text-xl font-bold">{index + 1}</span>
                    </div>
                    <div>
                      <h3 className="mb-2 text-xl font-bold text-gray-800">
                        {step.title}
                      </h3>
                      <p className="text-gray-600">{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-12 rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 p-0.5 shadow-sm">
                <div className="rounded-lg bg-white p-6">
                  <div className="flex flex-col items-center justify-between sm:flex-row">
                    <div>
                      <h3 className="mb-2 text-xl font-bold text-gray-800">
                        Ready to get started?
                      </h3>
                      <p className="text-gray-600">
                        Join thousands of students already using PetroX
                      </p>
                    </div>
                    <Link
                      to="/signup"
                      className="mt-4 rounded bg-indigo-600 px-8 py-3 font-medium text-white transition-all hover:bg-indigo-700 sm:mt-0"
                    >
                      Sign Up Free
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section
        id="testimonials"
        className="bg-gray-900 px-6 py-20 text-white md:px-12"
      >
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold md:text-4xl">
              What Students Say
            </h2>
            <p className="mx-auto max-w-2xl text-gray-400">
              Hear from students who have transformed their academic journey
              with PetroX
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {testimonials.map((testimonial, index) => (
              <div
                key={index}
                className="rounded-lg border border-gray-700 bg-gray-800 p-6"
              >
                <div className="mb-6 flex items-center">
                  <div className="mr-4 flex h-12 w-12 items-center justify-center rounded-full bg-gray-700">
                    <span className="text-lg font-medium text-indigo-400">
                      {testimonial.name.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-lg font-bold">{testimonial.name}</h4>
                    <p className="text-gray-400">{testimonial.role}</p>
                  </div>
                </div>
                <p className="mb-4 text-gray-300">"{testimonial.quote}"</p>
                <div className="flex text-amber-400">
                  {[...Array(5)].map((_, i) => (
                    <svg
                      key={i}
                      className="h-4 w-4 fill-current"
                      viewBox="0 0 24 24"
                    >
                      <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                    </svg>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Assistant Section */}
      <section className="bg-white px-6 py-20 md:px-12">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col items-center gap-12 lg:flex-row">
            <div className="lg:w-1/2">
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <div className="mb-6 flex items-center">
                  <div className="mr-4 flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
                    <FaRobot className="text-xl" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">
                      PetroMark AI Assistant
                    </h3>
                    <p className="text-gray-600">
                      Your personal learning companion
                    </p>
                  </div>
                </div>

                <div className="mb-6 space-y-4">
                  <div className="flex items-start">
                    <div className="mr-3 flex h-8 w-8 items-center justify-center rounded-full border border-gray-300 bg-gray-100 text-sm">
                      AI
                    </div>
                    <div className="rounded-lg rounded-tl-none bg-indigo-50 p-4">
                      <p className="text-gray-800">
                        How can I help with your studies today?
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start justify-end">
                    <div className="max-w-xs rounded-lg rounded-tr-none bg-indigo-600 p-4 text-white">
                      <p>Can you explain quantum physics concepts?</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <p className="mb-3 font-medium text-gray-700">
                    PetroMark is ready to assist with:
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {aiFeatures.map((feature, index) => (
                      <div key={index} className="flex items-center">
                        <div className="mr-2 h-1.5 w-1.5 rounded-full bg-indigo-600"></div>
                        <span className="text-sm text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:w-1/2">
              <h2 className="mb-6 text-3xl font-bold text-gray-800 md:text-4xl">
                Intelligent Learning with{' '}
                <span className="text-indigo-600">PetroMark AI</span>
              </h2>
              <p className="mb-8 text-gray-600">
                Our advanced AI assistant provides personalized tutoring,
                answers your questions in real-time, and helps you master
                complex subjects through interactive learning.
              </p>

              <ul className="mb-8 space-y-4">
                {aiBenefits.map((benefit, index) => (
                  <li key={index} className="flex items-start">
                    <div className="mt-1 mr-3 rounded-full bg-indigo-100 p-1 text-indigo-600">
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeWidth="2"
                          d="M5 13l4 4L19 7"
                        ></path>
                      </svg>
                    </div>
                    <span className="text-gray-700">{benefit}</span>
                  </li>
                ))}
              </ul>

              <Link
                to="/petromark"
                className="inline-flex items-center rounded bg-indigo-600 px-8 py-3 font-medium text-white transition-all hover:bg-indigo-700"
              >
                <FaRobot className="mr-2" />
                Try PetroMark Now
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 px-6 pt-16 pb-8 text-white md:px-12">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 grid grid-cols-1 gap-8 md:grid-cols-4">
            <div>
              <h3 className="mb-4 text-2xl font-bold">
                <span className="text-indigo-400">PETRO</span>
                <span className="text-amber-400">X</span>
              </h3>
              <p className="mb-6 text-gray-400">
                The ultimate academic platform for students seeking excellence.
              </p>
              <div className="flex space-x-4">
                {socialLinks.map((social, index) => (
                  <a
                    key={index}
                    href={social.url}
                    className="flex h-8 w-8 items-center justify-center rounded bg-gray-800 text-gray-300 transition-colors hover:bg-gray-700"
                    aria-label={social.name}
                  >
                    {social.icon}
                  </a>
                ))}
              </div>
            </div>

            <div>
              <h4 className="mb-4 text-lg font-bold text-gray-200">
                Resources
              </h4>
              <ul className="space-y-2">
                {resources.map((resource, index) => (
                  <li key={index}>
                    <a
                      href={resource.url}
                      className="text-gray-400 transition-colors hover:text-white"
                    >
                      {resource.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="mb-4 text-lg font-bold text-gray-200">Features</h4>
              <ul className="space-y-2">
                {featureLinks.map((feature, index) => (
                  <li key={index}>
                    <a
                      href={feature.url}
                      className="text-gray-400 transition-colors hover:text-white"
                    >
                      {feature.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="mb-4 text-lg font-bold text-gray-200">
                Stay Updated
              </h4>
              <p className="mb-4 text-gray-400">
                Subscribe to our newsletter for updates
              </p>
              <div className="flex">
                <input
                  type="email"
                  placeholder="Your email"
                  className="w-full rounded-l bg-gray-800 px-4 py-2 text-white focus:outline-none"
                />
                <button className="rounded-r bg-indigo-600 px-4 py-2 text-white transition-colors hover:bg-indigo-700">
                  Subscribe
                </button>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-500">
            <p>
              &copy; {new Date().getFullYear()} PetroX. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Data arrays
const features = [
  {
    icon: <FaBook />,
    title: 'Study Materials',
    description:
      'Access thousands of resources, textbooks, and past questions for all subjects.',
    tags: ['Resources', 'Textbooks', 'Past Questions']
  },
  {
    icon: <FaUsers />,
    title: 'Group Tests',
    description:
      'Create and join collaborative tests with peers to prepare for exams.',
    tags: ['Collaborative', 'Real-time', 'Custom Tests']
  },
  {
    icon: <FaComments />,
    title: 'Live Chat',
    description:
      'Connect with other students for study sessions and discussions.',
    tags: ['Real-time', 'Study Groups', 'Collaboration']
  },
  {
    icon: <FaCalculator />,
    title: 'GP Calculator',
    description:
      'Calculate your GPA and CGPA instantly with our academic calculator.',
    tags: ['GPA', 'CGPA', 'Tracking']
  },
  {
    icon: <FaFileUpload />,
    title: 'Material Upload',
    description:
      'Share study materials and earn recognition for contributions.',
    tags: ['Upload', 'Badges', 'Community']
  },
  {
    icon: <FaGraduationCap />,
    title: 'Past Questions',
    description: 'Access past exam questions with solutions and analytics.',
    tags: ['Exams', 'Solutions', 'Analytics']
  }
];

const steps = [
  {
    title: 'Create Your Profile',
    description: 'Set up your academic profile in minutes'
  },
  {
    title: 'Access Resources',
    description: 'Browse our library of textbooks and study materials'
  },
  {
    title: 'Join Study Groups',
    description: 'Connect with peers and create collaborative sessions'
  },
  {
    title: 'Track Progress',
    description: 'Use our tools to monitor your academic journey'
  }
];

const testimonials = [
  {
    name: 'Sarah Johnson',
    role: 'Medical Student',
    quote:
      'PetroX transformed how I prepare for exams. The group tests feature helped me collaborate effectively.'
  },
  {
    name: 'David Chen',
    role: 'Engineering Student',
    quote:
      'The GP calculator and PetroMark AI have been game-changers. Improved my GPA significantly.'
  },
  {
    name: 'Amanda Rodriguez',
    role: 'Law Student',
    quote:
      'Finding quality study materials used to take hours. With PetroX, everything is in one place.'
  }
];

const aiFeatures = [
  'Concept Explanations',
  'Homework Help',
  'Study Planning',
  'Practice Questions',
  'Research Assistance',
  'Exam Preparation'
];

const aiBenefits = [
  '24/7 personalized tutoring in any subject',
  'Instant answers to complex questions',
  'Adaptive learning paths based on progress',
  'Comprehensive explanations with examples',
  'Study recommendations based on syllabus'
];

const socialLinks = [
  { name: 'Facebook', icon: 'FB', url: '#' },
  { name: 'Twitter', icon: 'TW', url: '#' },
  { name: 'Instagram', icon: 'IG', url: '#' },
  { name: 'LinkedIn', icon: 'IN', url: '#' }
];

const resources = [
  { name: 'Blog', url: '#' },
  { name: 'Help Center', url: '#' },
  { name: 'Community', url: '#' },
  { name: 'Study Guides', url: '#' }
];

const featureLinks = [
  { name: 'Study Materials', url: '#' },
  { name: 'Group Tests', url: '#' },
  { name: 'Live Chat', url: '#' },
  { name: 'GP Calculator', url: '#' },
  { name: 'PetroMark AI', url: '#' }
];

export default LandingPage;
