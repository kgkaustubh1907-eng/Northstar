import React, { lazy, Suspense, useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { getMe, logout } from './services/api';
import Shell from './components/Shell';
import { Loading } from './components/UI';

const Login = lazy(() => import('./pages/Login'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const PatientList = lazy(() =>
  import('./pages/Patients').then((module) => ({ default: module.PatientList })),
);
const PatientDetails = lazy(() =>
  import('./pages/Patients').then((module) => ({ default: module.PatientDetails })),
);
const ResourcePage = lazy(() =>
  import('./pages/Resources').then((module) => ({ default: module.ResourcePage })),
);
const DoctorDirectory = lazy(() =>
  import('./pages/Resources').then((module) => ({ default: module.DoctorDirectory })),
);
const DepartmentDirectory = lazy(() =>
  import('./pages/Resources').then((module) => ({ default: module.DepartmentDirectory })),
);
const CaretakersPage = lazy(() =>
  import('./pages/Resources').then((module) => ({ default: module.CaretakersPage })),
);
const QueryCenter = lazy(() => import('./pages/QueryCenter'));

function Secure({ user, children }) {
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(!!localStorage.getItem('access'));

  useEffect(() => {
    if (localStorage.getItem('access')) {
      getMe()
        .then(setUser)
        .catch(() => {
          logout();
          setUser(null);
        })
        .finally(() => setChecking(false));
    }
  }, []);

  if (checking) {
    return (
      <div className="startup">
        <Loading label="Connecting to hospital workspace..." />
      </div>
    );
  }

  const login = (currentUser) => {
    setUser(currentUser);
    localStorage.setItem('displayName', currentUser.name);
  };

  return (
    <Suspense
      fallback={
        <div className="startup">
          <Loading label="Loading hospital workspace..." />
        </div>
      }
    >
      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/" replace /> : <Login onLogin={login} />}
        />
        <Route
          path="/"
          element={
            <Secure user={user}>
              <Shell user={user} />
            </Secure>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="patients" element={<PatientList />} />
          <Route path="patients/:id" element={<PatientDetails />} />
          <Route path="doctors" element={<DoctorDirectory />} />
          <Route path="departments" element={<DepartmentDirectory />} />
          <Route path="diagnoses" element={<ResourcePage kind="diagnoses" />} />
          <Route path="tests" element={<ResourcePage kind="tests" />} />
          <Route path="prescriptions" element={<ResourcePage kind="prescriptions" />} />
          <Route path="medical-stores" element={<ResourcePage kind="medical-stores" />} />
          <Route path="equipment" element={<ResourcePage kind="equipment" />} />
          <Route path="caretakers" element={<CaretakersPage />} />
          <Route path="query" element={<QueryCenter />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
