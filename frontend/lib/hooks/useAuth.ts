import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api/client';
import { useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_verified: boolean;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });
  const router = useRouter();

  // Check auth status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      setState({ user: null, isLoading: false, isAuthenticated: false });
      return;
    }

    try {
      const response = await api.auth.me();
      setState({
        user: response.data,
        isLoading: false,
        isAuthenticated: true,
      });
    } catch (error) {
      localStorage.removeItem('access_token');
      setState({ user: null, isLoading: false, isAuthenticated: false });
    }
  };

  const login = useCallback(async (email: string, password: string) => {
    try {
      const response = await api.auth.login(email, password);
      const { access_token, refresh_token, user } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
      });
      
      toast.success('Welcome back!');
      
      // Redirect based on role
      switch (user.role) {
        case 'learner':
          router.push('/learner');
          break;
        case 'teacher':
          router.push('/teacher');
          break;
        case 'parent':
          router.push('/parent');
          break;
        default:
          router.push('/');
      }
      
      return { success: true };
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
      return { success: false, error: message };
    }
  }, [router]);

  const register = useCallback(async (data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    school_id?: string;
  }) => {
    try {
      const response = await api.auth.register(data);
      toast.success('Registration successful! Please check your email.');
      return { success: true, data: response.data };
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed';
      toast.error(message);
      return { success: false, error: message };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      // Ignore error
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setState({ user: null, isLoading: false, isAuthenticated: false });
      router.push('/login');
      toast.success('Logged out successfully');
    }
  }, [router]);

  return {
    ...state,
    login,
    register,
    logout,
    refresh: checkAuth,
  };
}
