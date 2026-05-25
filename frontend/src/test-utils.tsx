import type { ReactNode } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, type To } from "react-router-dom";

interface WrapperOptions {
  initialEntries?: (string | Partial<{ pathname: string; state: unknown }>)[];
}

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(
  ui: ReactNode,
  options?: RenderOptions & WrapperOptions,
) {
  const { initialEntries = ["/"], ...renderOptions } = options ?? {};
  const queryClient = createTestQueryClient();

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries as To[]}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    );
  }

  return { ...render(ui, { wrapper: Wrapper, ...renderOptions }), queryClient };
}

export function mockJsonResponse<T>(data: T): Response {
  return {
    ok: true,
    json: () => Promise.resolve(data),
    status: 200,
  } as unknown as Response;
}
