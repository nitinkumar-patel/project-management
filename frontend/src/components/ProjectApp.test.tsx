import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProjectApp } from "@/components/ProjectApp";
import { initialData } from "@/lib/kanban";

const signIn = async () => {
  await userEvent.type(screen.getByLabelText(/username/i), "user");
  await userEvent.type(screen.getByLabelText(/password/i), "password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

describe("ProjectApp", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => initialData,
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the login screen before sign in", () => {
    render(<ProjectApp />);

    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /kanban studio/i })
    ).not.toBeInTheDocument();
  });

  it("shows an error for invalid credentials", async () => {
    render(<ProjectApp />);

    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "credentials");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Invalid username or password."
    );
    expect(
      screen.queryByRole("heading", { name: /kanban studio/i })
    ).not.toBeInTheDocument();
  });

  it("shows the board after successful login", async () => {
    render(<ProjectApp />);

    await signIn();

    expect(
      screen.getByRole("heading", { name: /kanban studio/i })
    ).toBeInTheDocument();
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("logs out and clears the session", async () => {
    render(<ProjectApp />);

    await signIn();
    await screen.findAllByTestId(/column-/i);
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(window.sessionStorage.getItem("project-management-authenticated")).toBeNull();
  });
});
