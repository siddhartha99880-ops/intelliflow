"use client";

import { create } from "zustand";

type AuthState = {
  token: string | null;
  email: string | null;
  setToken: (token: string | null) => void;
  setEmail: (email: string | null) => void;
  clear: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  email: null,
  setToken: (token) => set({ token }),
  setEmail: (email) => set({ email }),
  clear: () => set({ token: null, email: null }),
}));

