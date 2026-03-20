import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Nav from "./Nav";

describe("Nav", () => {
  it("renders brand link", () => {
    render(<Nav />);
    expect(screen.getByText("Storybook Library")).toBeDefined();
    expect(screen.getByRole("link", { name: /storybook library/i })).toBeDefined();
  });

  it("renders desktop navigation links", () => {
    render(<Nav />);
    const links = screen.getAllByText("Browse");
    expect(links.length).toBeGreaterThanOrEqual(1);
  });

  it("mobile menu is hidden by default", () => {
    render(<Nav />);
    const menu = screen.getByRole("menu", { hidden: true });
    expect(menu.getAttribute("aria-hidden")).toBe("true");
    expect(menu.classList.contains("hidden")).toBe(true);
  });

  it("toggles mobile menu on hamburger click", () => {
    render(<Nav />);
    const toggle = screen.getByLabelText("Toggle navigation menu");

    expect(toggle.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");

    const menu = screen.getByRole("menu");
    expect(menu.getAttribute("aria-hidden")).toBe("false");
    expect(menu.classList.contains("hidden")).toBe(false);
  });

  it("closes mobile menu when link is clicked", () => {
    render(<Nav />);
    const toggle = screen.getByLabelText("Toggle navigation menu");
    fireEvent.click(toggle);

    // Menu is now visible
    const menuLinks = screen.getByRole("menu").querySelectorAll("a");
    fireEvent.click(menuLinks[0]);

    // Menu should be hidden again
    const menu = screen.getByRole("menu", { hidden: true });
    expect(menu.getAttribute("aria-hidden")).toBe("true");
  });

  it("hamburger button has aria-controls", () => {
    render(<Nav />);
    const toggle = screen.getByLabelText("Toggle navigation menu");
    expect(toggle.getAttribute("aria-controls")).toBe("mobile-nav-menu");
  });

  it("mobile menu items have role=menuitem", () => {
    render(<Nav />);
    // Open menu first so items are accessible
    const toggle = screen.getByLabelText("Toggle navigation menu");
    fireEvent.click(toggle);
    const menuitems = screen.getAllByRole("menuitem");
    expect(menuitems.length).toBe(3);
  });
});
