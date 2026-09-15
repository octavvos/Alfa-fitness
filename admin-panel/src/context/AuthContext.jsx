import { createContext, useContext, useEffect, useState } from "react";
import { getTokens, clearTokens } from "../api/client";
import { getMe, login as loginRequest } from "../api/endpoints";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tokens = getTokens();
    if (!tokens?.access) {
      setLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => {
        clearTokens();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(username, password) {
    await loginRequest(username, password);
    const me = await getMe();
    if (me.role !== "admin") {
      clearTokens();
      throw new Error("Bu panel faqat administratorlar uchun.");
    }
    setUser(me);
    return me;
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
