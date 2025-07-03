export default function Settings() {
  return (
    <div className="mx-auto max-w-3xl rounded-xl bg-gray-50 p-4 shadow-md md:p-6">
      <h2 className="mb-4 text-xl font-semibold text-gray-800 md:mb-6">
        Account Settings
      </h2>

      <div className="space-y-4 md:space-y-6">
        <div>
          <h3 className="mb-2 text-base font-medium text-gray-800 md:mb-3 md:text-lg">
            Profile Information
          </h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 md:gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700 md:text-base">
                First Name
              </label>
              <input
                type="text"
                defaultValue="John"
                className="w-full rounded-lg border border-gray-300 px-4 py-2"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700 md:text-base">
                Last Name
              </label>
              <input
                type="text"
                defaultValue="Doe"
                className="w-full rounded-lg border border-gray-300 px-4 py-2"
              />
            </div>
          </div>
        </div>

        <div>
          <h3 className="mb-2 text-base font-medium text-gray-800 md:mb-3 md:text-lg">
            Notification Preferences
          </h3>
          <div className="space-y-2 md:space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                defaultChecked
                className="h-4 w-4 rounded text-blue-600"
              />
              <label className="ml-2 text-sm text-gray-700 md:text-base">
                Email notifications
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                defaultChecked
                className="h-4 w-4 rounded text-blue-600"
              />
              <label className="ml-2 text-sm text-gray-700 md:text-base">
                Push notifications
              </label>
            </div>
          </div>
        </div>

        <div className="pt-2">
          <button className="rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 px-5 py-2.5 font-medium text-white transition hover:from-blue-700 hover:to-blue-800">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
