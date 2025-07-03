import { useEffect } from 'react';

const PetroMarkAI = () => {
  useEffect(() => {
    const existingScript = document.querySelector(
      'script[src="https://unpkg.com/@elevenlabs/convai-widget-embed"]'
    );

    if (!existingScript) {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/@elevenlabs/convai-widget-embed';
      script.async = true;
      script.type = 'text/javascript';
      document.head.appendChild(script);
    }

    return () => {
      // Clean up if needed
    };
  }, []);

  return (
    <div className="h-[calc(100vh-200px)] rounded-xl bg-gray-50 p-4 shadow-md md:p-6">
      <div className="mb-4 flex items-center md:mb-6">
        <div className="mr-3 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 p-2 md:mr-4 md:p-3">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-white md:h-8 md:w-8"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-800 md:text-2xl">
            PetroMark AI Assistant
          </h2>
          <p className="text-sm text-gray-600 md:text-base">
            Your intelligent learning companion
          </p>
        </div>
      </div>

      <div className="h-[calc(100%-80px)] overflow-hidden rounded-lg border">
        <div className="flex h-full flex-col">
          <div className="flex-1 overflow-hidden">
            <elevenlabs-convai agent-id="agent_01jx3tjzhyfjnt6cxax880pxx4"></elevenlabs-convai>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PetroMarkAI;
