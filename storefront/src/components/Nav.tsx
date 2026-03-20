"use client";

import { useState } from "react";

export default function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
      <a href="/" className="flex items-center gap-2">
        <span className="text-2xl" aria-hidden="true">📚</span>
        <span className="font-display text-xl font-bold text-primary-800">
          Storybook Library
        </span>
      </a>
      {/* Desktop links */}
      <div className="hidden md:flex items-center gap-6">
        <a href="/#catalog" className="text-sm text-gray-600 hover:text-primary-700 transition-colors">Browse</a>
        <a href="/#narrators" className="text-sm text-gray-600 hover:text-primary-700 transition-colors">Narrators</a>
        <a href="/#about" className="text-sm text-gray-600 hover:text-primary-700 transition-colors">About</a>
      </div>
      {/* Mobile hamburger */}
      <button
        className="md:hidden p-2 text-gray-600 hover:text-gray-900"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls="mobile-nav-menu"
        aria-label="Toggle navigation menu"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          {open ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>
      {/* Mobile menu */}
      <div
        id="mobile-nav-menu"
        role="menu"
        aria-hidden={!open}
        className={`absolute top-full left-0 right-0 bg-white border-b border-gray-100 shadow-lg md:hidden z-50 ${open ? "" : "hidden"}`}
      >
        <div className="flex flex-col p-4 gap-3">
          <a href="/#catalog" role="menuitem" className="text-sm text-gray-600 hover:text-primary-700 py-2" onClick={() => setOpen(false)}>Browse</a>
          <a href="/#narrators" role="menuitem" className="text-sm text-gray-600 hover:text-primary-700 py-2" onClick={() => setOpen(false)}>Narrators</a>
          <a href="/#about" role="menuitem" className="text-sm text-gray-600 hover:text-primary-700 py-2" onClick={() => setOpen(false)}>About</a>
        </div>
      </div>
    </nav>
  );
}
