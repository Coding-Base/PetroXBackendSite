import {  Button } from '../components/ui/button'

function SideMenu() {
  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };
  return (
    <div className="hidden flex-col bg-blue-800 p-6 text-white md:flex md:w-64">
      <div className="mb-8 flex justify-center">
        <img src={logo} alt="Petrox logo" className="h-24 object-contain" />
      </div>

      <div className="flex-1 space-y-3">
        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'dashboard' ? 'bg-blue-600' : 'hover:bg-blue-700'
          }`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>

        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'createTest' ? 'bg-blue-600' : 'hover:bg-blue-700'
          }`}
          onClick={() => {
            setActiveTab('createTest');
            setShowTestForm(true);
          }}
        >
          Create Test
        </button>

        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'createGroupTest'
              ? 'bg-blue-600'
              : 'hover:bg-blue-700'
          }`}
          onClick={() => {
            setActiveTab('createGroupTest');
            navigate('/create-group');
          }}
        >
          Create Group Test
        </button>
        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'UploadPastQuestions'
              ? 'bg-blue-600'
              : 'hover:bg-blue-700'
          }`}
          onClick={() => {
            setActiveTab('UploadPastQuestions');
            navigate('/upload');
            setShowMobileMenu(false);
          }}
        >
          Upload Past Questions
        </button>

        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'MaterialManagement'
              ? 'bg-blue-600'
              : 'hover:bg-blue-700'
          }`}
          onClick={() => {
            setActiveTab('MaterialManagement');
            navigate('/material');
          }}
        >
          Material Management
        </button>

        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'petromark' ? 'bg-blue-600' : 'hover:bg-blue-700'
          }`}
          onClick={() => setActiveTab('petromark')}
        >
          PetroMark AI
        </button>

        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'history' ? 'bg-blue-600' : 'hover:bg-blue-700'
          }`}
          onClick={() => {
            setActiveTab('history');
          }}
        >
          History
        </button>

        <button
          className={`w-full rounded-lg px-4 py-3 text-left transition ${
            activeTab === 'settings' ? 'bg-blue-600' : 'hover:bg-blue-700'
          }`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </div>

      <div className="mt-auto">
        <button
          onClick={handleLogout}
          className="w-full rounded-lg px-4 py-3 text-left transition hover:bg-red-600"
        >
          Logout
        </button>
      </div>
    </div>
  );
}
