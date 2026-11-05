import { Route, Routes } from 'react-router';
import AppLayout from './components/AppLayout';
import HomePage from './components/HomePage';
import NotFoundPage from './components/NotFoundPage';

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
