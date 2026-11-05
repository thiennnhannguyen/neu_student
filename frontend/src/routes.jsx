import AppLayout from './components/AppLayout';
import HomePage from './components/HomePage';
import NotFoundPage from './components/NotFoundPage';

export const routes = [
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];
