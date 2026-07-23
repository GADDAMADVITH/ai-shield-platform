import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  getStoredUser,
  isAuthenticated as readIsAuthenticated,
  login as persistLogin,
  logout as persistLogout,
  updateStoredUser,
  type AuthUser,
} from "@/lib/auth";

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (remember?: boolean, overrides?: Partial<AuthUser>) => AuthUser;
  logout: () => void;
  updateUser: (partial: Partial<AuthUser>) => AuthUser | null;
  refresh: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);

  const refresh = useCallback(() => {
    if (!readIsAuthenticated()) {
      setUser(null);
      return;
    }
    setUser(getStoredUser());
  }, []);

  useEffect(() => {
    refresh();
    setHydrated(true);
  }, [refresh]);

  const login = useCallback((remember = true, overrides: Partial<AuthUser> = {}) => {
    const next = persistLogin(remember, overrides);
    setUser(next);
    return next;
  }, []);

  const logout = useCallback(() => {
    persistLogout();
    setUser(null);
  }, []);

  const updateUser = useCallback((partial: Partial<AuthUser>) => {
    const next = updateStoredUser(partial);
    if (next) setUser(next);
    return next;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: hydrated ? user : getStoredUser(),
      isAuthenticated: hydrated ? !!user : readIsAuthenticated(),
      login,
      logout,
      updateUser,
      refresh,
    }),
    [hydrated, user, login, logout, updateUser, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
