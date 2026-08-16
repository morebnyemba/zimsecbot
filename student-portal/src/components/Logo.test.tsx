import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Logo } from "./Logo";

describe("Logo", () => {
  it("renders the wordmark by default", () => {
    render(<Logo />);
    expect(screen.getByText("fundi")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Zimfundi" })).toBeInTheDocument();
  });

  it("omits the wordmark when withWordmark is false", () => {
    render(<Logo withWordmark={false} />);
    expect(screen.queryByText("fundi")).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Zimfundi" })).toBeInTheDocument();
  });
});
