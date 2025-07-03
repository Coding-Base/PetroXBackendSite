import NotFound from '../pages/NotFound';
import { Suspense, lazy } from 'react';
import { Navigate, Outlet, useRoutes } from 'react-router-dom';

const NewDashboardLayout = lazy(() => import('../Layouts/dashboardlayout'));
const SignIn = lazy(() => import('../pages/SignIn'));
const Settings = lazy(() => import('../pages/Settings'));
const SignUp = lazy(() => import('../pages/Signup'));
const DashboardPage = lazy(() => import('../Layouts/dashboard'));
const Chat = lazy(() => import('../pages/chat'));
const CreateGroupTest = lazy(() => import('../pages/CreateGroupTest'));
const GroupTestPage = lazy(() => import('../pages/GroupTestPage'));
const MyTest = lazy(() => import('../pages/MyTests'));
const Test = lazy(() => import('../pages/Test'));
const GroupTest = lazy(() => import('../pages/GroupTestPage'));
const PastQuestions = lazy(() => import('../pages/PastQuestions'));
const LandingPage = lazy(() => import('../pages/LandingPage'));
const PetroMarkAI = lazy(() => import('../pages/Petromark'));
const MaterialsManagement = lazy(() => import('../pages/MaterialsManagement'));
const Tools = lazy(() => import('../Layouts/ToolPage'));
// ----------------------------------------------------------------------

export default function AppRouter() {
  const dashboardRoutes = [
    {
      path: '/dashboard',
      element: (
        <NewDashboardLayout>
          <Suspense>
            <Outlet />
          </Suspense>
        </NewDashboardLayout>
      ),
      children: [
        {
          element: <DashboardPage />,
          index: true
        },
        {
          path: 'group-test/:testId',
          element: <GroupTestPage />
        },
        {
          path: 'past-questions',
          element: <PastQuestions />
        },
        {
          path: 'my-tests',
          element: <MyTest />
        },
        {
          path: 'tests',
          element: <Test />
        },
        {
          path: 'materials-management',
          element: <MaterialsManagement />
        },
        {
          path: 'create-group-test',
          element: <CreateGroupTest />
        },
        {
          path: 'petromark-ai',
          element: <PetroMarkAI />
        },
        {
          path: 'tools',
          element: <Tools/>
        },
        {
          path: 'chat',
          element: <Chat />
        },
        {
          path: 'settings',
          element: <Settings />
        }
      ]
    }
  ];

  const publicRoutes = [
    {
      path: '/',
      element: <LandingPage />,
      index: true
    },
    {
      path: '/login',
      element: <SignIn />,
      index: true
    },
    {
      path: '/signup',
      element: <SignUp />,
      index: true
    },
    {
      path: '/404',
      element: <NotFound />
    }
    // {
    //   path: '*',
    //   element: <Navigate to="/404" replace />
    // }
  ];

  const routes = useRoutes([...dashboardRoutes, ...publicRoutes]);

  return routes;
}
