import { useRouter } from '../routes/hooks';
import { Button } from '../components/ui/button';

export default function NotFound() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50 p-4">
      <div className="max-w-md w-full text-center">
        {/* Animated illustration */}
        <div className="relative mx-auto mb-8 w-64 h-64">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-48 h-48 rounded-full bg-indigo-100 animate-pulse"></div>
          </div>
          <div className="relative z-10 flex flex-col items-center">
            <div className="w-32 h-32 rounded-full bg-white border-8 border-indigo-200 flex items-center justify-center">
              <div className="text-6xl">😕</div>
            </div>
            <div className="mt-4">
              <div className="w-16 h-4 bg-indigo-300 rounded-full animate-bounce mx-auto"></div>
              <div className="w-24 h-4 bg-indigo-300 rounded-full animate-bounce mx-auto mt-2" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>

        {/* Content */}
        <h1 className="text-8xl md:text-9xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600 mb-4">
          404
        </h1>
        
        <h2 className="text-2xl md:text-3xl font-bold text-gray-800 mb-3">
          Oops! Page Not Found
        </h2>
        
        <p className="text-gray-600 mb-8 max-w-md mx-auto">
          The page you're looking for might have been moved, removed, or doesn't exist. 
          Let's get you back on track.
        </p>
        
        <div className="flex flex-col sm:flex-row justify-center gap-3">
          <Button 
            onClick={() => router.back()}
            className="py-6 text-base bg-indigo-600 hover:bg-indigo-700 transition-all transform hover:-translate-y-0.5 shadow-lg hover:shadow-xl"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Go Back
          </Button>
          
          <Button 
            onClick={() => router.push('/dashboard')}
            variant="outline"
            className="py-6 text-base border-indigo-600 text-indigo-600 hover:bg-indigo-50 transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Dashboard Home
          </Button>
        </div>
        
        <div className="mt-12 pt-6 border-t border-gray-200">
          <p className="text-gray-500 text-sm">
            Need help? <a href="/support" className="text-indigo-600 hover:underline">Contact support</a>
          </p>
        </div>
      </div>
    </div>
  );
}