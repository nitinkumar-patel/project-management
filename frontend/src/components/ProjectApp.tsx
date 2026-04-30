"use client";

import { useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";

const SESSION_KEY = "project-management-authenticated";

const readSession = () => {
  if (typeof window === "undefined") {
    return false;
  }

  return window.sessionStorage.getItem(SESSION_KEY) === "true";
};

export const ProjectApp = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(readSession);

  const handleLogin = () => {
    window.sessionStorage.setItem(SESSION_KEY, "true");
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    window.sessionStorage.removeItem(SESSION_KEY);
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return <KanbanBoard onLogout={handleLogout} />;
};
