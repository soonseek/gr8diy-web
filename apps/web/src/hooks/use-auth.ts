import { useAuthStore } from "@/stores/auth-store";
import type { User } from "@gr8diy/types";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useAuth() {
  const { user, isAuthenticated, setAuth, clearAuth, accessToken } = useAuthStore();

  const login = async (email: string, password: string) => {
    const response = await axios.post(`${API_URL}/api/v1/auth/login`, {
      email,
      password,
    }, { withCredentials: true });

    const { access_token, user: userData } = response.data;

    // Store access_token in localStorage (but NOT refresh_token - it's in httpOnly cookie)
    localStorage.setItem("access_token", access_token);
    setAuth(userData, access_token);
  };

  const logout = async () => {
    try {
      // Call logout endpoint to clear httpOnly cookie
      await axios.post(`${API_URL}/api/v1/auth/logout`, {}, { withCredentials: true });
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear local storage
      localStorage.removeItem("access_token");
      clearAuth();
    }
  };

  return {
    user,
    isAuthenticated,
    accessToken,
    login,
    logout,
  };
}
