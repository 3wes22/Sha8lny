import type { ReactNode } from "react";
import { describe, it, expect, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '@/test/utils';
import LoginPage from './LoginPage';

// Mock the AuthContext
vi.mock('@/features/auth/context/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn(),
    isLoading: false,
    user: null,
  }),
  AuthProvider: ({ children }: { children: ReactNode }) => children,
}));

describe('Login Page', () => {
  it('renders the login form', () => {
    render(<LoginPage />);

    // Check for main elements
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders the logo and welcome message', () => {
    render(<LoginPage />);

    expect(screen.getByText('Sha8alny')).toBeInTheDocument();
    expect(screen.getByText('Welcome back')).toBeInTheDocument();
  });

  it('has a link to register page', () => {
    render(<LoginPage />);

    expect(screen.getByRole('link', { name: /sign up/i })).toHaveAttribute('href', '/register');
  });

  it('allows user to type in email and password fields', async () => {
    render(<LoginPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('has password field with type password by default', () => {
    render(<LoginPage />);

    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });
});
