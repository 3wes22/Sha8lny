import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

const browserRouterProps = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", () => ({
  BrowserRouter: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
    browserRouterProps(props);
    return <div data-testid="browser-router">{children}</div>;
  },
}));

vi.mock("@/features/auth/context/AuthContext", () => ({
  AuthProvider: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

import { AppProviders } from "@/app/AppProviders";

describe("AppProviders", () => {
  it("opts into the React Router v7 future flags", () => {
    render(
      <AppProviders>
        <div>content</div>
      </AppProviders>,
    );

    expect(screen.getByText("content")).toBeInTheDocument();
    expect(browserRouterProps).toHaveBeenCalledWith({
      future: {
        v7_relativeSplatPath: true,
        v7_startTransition: true,
      },
    });
  });
});
