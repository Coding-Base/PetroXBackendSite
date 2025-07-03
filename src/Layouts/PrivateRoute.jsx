// src/components/PrivateRoute.jsx
import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

export default function PrivateRoute() {
  const token = localStorage.getItem('access_token');
  const location = useLocation();

  // If we have a token, render child routes; otherwise redirect to /signin
  return token ? (
    <Outlet />
  ) : (
    <Navigate
      to={`/login?next=${location.pathname}${location.search}`} // Preserve the current path and query params
      replace
    />
  );
}
