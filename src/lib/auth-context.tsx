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
  fetchCurrentUser,
  getStoredUser,
  isAuthenticated as readIsAuthenticated,
  loginWithCredentials,
  logout as persistLogout,
  registerAccount,
  updateStoredUser,
  type AuthUser,
} from "@/lib/auth";
import { messageForApiError } from "@/lib/api/errors";

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  bootstrapping: boolean;
  login: (email: string, password: string, remember?: boolean) => Promise<AuthUser>;
  register: (fullName: string, email: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
  updateUser: (partial: Partial<AuthUser>) => AuthUser | null;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [bootstrapping, setBootstrapping] = useState(true);

  const refresh = useCallback(async () => {
    if (!readIsAuthenticated()) {
      setUser(null);
      return;
    }
    try {
      const me = await fetchCurrentUser();
      setUser(me);
    } catch {
      setUser(getStoredUser());
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!readIsAuthenticated()) {
        if (!cancelled) {
          setUser(null);
          setBootstrapping(false);
        }
        return;
      }
      // Show cached user immediately, then confirm with /me
      if (!cancelled) setUser(getStoredUser());
      try {
        const me = await fetchCurrentUser();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) {
          // Token invalid — clear session
          await persistLogout();
          setUser(null);
        }
      } finally {
        if (!cancelled) setBootstrapping(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string, remember = true) => {
    const next = await loginWithCredentials(email, password, remember);
    setUser(next);
    return next;
  }, []);

  const register = useCallback(async (fullName: string, email: string, password: string) => {
    const next = await registerAccount(fullName, email, password, true);
    setUser(next);
    return next;
  }, []);

  const logout = useCallback(async () => {
    try {
      await persistLogout();
    } catch (error) {
      console.warn(messageForApiError(error));
    }
    setUser(null);
  }, []);

  const updateUser = useCallback((partial: Partial<AuthUser>) => {
    const next = updateStoredUser(partial);
    if (next) setUser(next);
    return next;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user && readIsAuthenticated(),
      bootstrapping,
      login,
      register,
      logout,
      updateUser,
      refresh,
    }),
    [user, bootstrapping, login, register, logout, updateUser, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
