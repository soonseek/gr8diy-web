import { useAuthStore } from "@/stores/auth-store";

export function useAuth() {
  const { user, isAuthenticated, setAuth, clearAuth, accessToken } = useAuthStore();

  const login = (user: any, accessToken: string, refreshToken: string) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    setAuth(user, accessToken, refreshToken);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    clearAuth();
  };

  return {
    user,
    isAuthenticated,
    accessToken,
    login,
    logout,
  };
}
