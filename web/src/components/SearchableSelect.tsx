import React, { useEffect, useId, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

export type SearchableSelectOption = {
  value: string;
  label: string;
};

type MenuPosition = {
  left: number;
  width: number;
  maxHeight: number;
  top?: number;
  bottom?: number;
};

type SearchableSelectProps = {
  label: string;
  value: string;
  options: readonly SearchableSelectOption[];
  onChange: (value: string) => void;
  searchPlaceholder: string;
  noResultsMessage: string;
  className?: string;
  style?: React.CSSProperties;
};

export default function SearchableSelect({
  label,
  value,
  options,
  onChange,
  searchPlaceholder,
  noResultsMessage,
  className = "glass-select",
  style,
}: SearchableSelectProps) {
  const generatedId = `searchable-select-${useId().replace(/:/g, "")}`;
  const listId = `${generatedId}-options`;
  const searchId = `${generatedId}-search`;
  const triggerRef = useRef<HTMLButtonElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const optionRefs = useRef<Array<HTMLLIElement | null>>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [menuPosition, setMenuPosition] = useState<MenuPosition>({
    left: 8,
    top: 8,
    width: 0,
    maxHeight: 320,
  });

  const selectedOption = options.find(option => option.value === value);
  const filteredOptions = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    if (!normalizedQuery) return options;
    return options.filter(option => option.label.toLocaleLowerCase().includes(normalizedQuery));
  }, [options, query]);

  const closeMenu = (restoreFocus = false) => {
    setIsOpen(false);
    setQuery("");
    setActiveIndex(-1);
    if (restoreFocus) triggerRef.current?.focus();
  };

  const openMenu = () => {
    setQuery("");
    const selectedIndex = options.findIndex(option => option.value === value);
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
    setIsOpen(true);
  };

  useEffect(() => {
    if (isOpen) searchRef.current?.focus();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const updatePosition = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;

      const viewportWidth = document.documentElement.clientWidth;
      const viewportHeight = window.innerHeight;
      const width = Math.min(rect.width, Math.max(0, viewportWidth - 16));
      const left = Math.max(8, Math.min(rect.left, viewportWidth - width - 8));
      const spaceAbove = rect.top - 8;
      const spaceBelow = viewportHeight - rect.bottom - 8;
      const openAbove = spaceBelow < 260 && spaceAbove > spaceBelow;
      const availableSpace = openAbove ? spaceAbove : spaceBelow;
      const maxHeight = Math.max(80, Math.min(320, availableSpace - 8));

      setMenuPosition({
        left,
        width,
        maxHeight,
        ...(openAbove
          ? { bottom: viewportHeight - rect.top + 6 }
          : { top: rect.bottom + 6 }),
      });
    };

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [isOpen]);

  useEffect(() => {
    if (activeIndex >= 0) {
      optionRefs.current[activeIndex]?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  useEffect(() => {
    if (!isOpen) return;

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target;
      if (
        target instanceof Node
        && !rootRef.current?.contains(target)
        && !menuRef.current?.contains(target)
      ) {
        closeMenu();
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [isOpen]);

  const moveActiveOption = (direction: 1 | -1) => {
    if (!filteredOptions.length) return;
    setActiveIndex(current => {
      if (current < 0) return direction > 0 ? 0 : filteredOptions.length - 1;
      return (current + direction + filteredOptions.length) % filteredOptions.length;
    });
  };

  const selectOption = (option: SearchableSelectOption) => {
    onChange(option.value);
    closeMenu(true);
  };

  const handleTriggerKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "Escape" && isOpen) {
      event.preventDefault();
      closeMenu(true);
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (isOpen) searchRef.current?.focus();
      else openMenu();
    }
  };

  const handleSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActiveOption(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActiveOption(-1);
    } else if (event.key === "Enter") {
      event.preventDefault();
      const option = filteredOptions[activeIndex];
      if (option) selectOption(option);
    } else if (event.key === "Escape") {
      event.preventDefault();
      closeMenu(true);
    }
  };

  const handleBlur = (event: React.FocusEvent<HTMLDivElement>) => {
    const target = event.relatedTarget;
    if (
      !(target instanceof Node)
      || (!rootRef.current?.contains(target) && !menuRef.current?.contains(target))
    ) {
      closeMenu();
    }
  };

  const menuStyle: React.CSSProperties = {
    left: menuPosition.left,
    width: menuPosition.width,
    maxHeight: menuPosition.maxHeight,
    ...(menuPosition.bottom !== undefined
      ? { bottom: menuPosition.bottom }
      : { top: menuPosition.top }),
  };

  return (
    <div className="searchable-select" ref={rootRef} onBlur={handleBlur}>
      <button
        ref={triggerRef}
        type="button"
        className={`searchable-select-trigger ${className}`}
        style={style}
        aria-label={`${label}: ${selectedOption?.label ?? value}`}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listId : undefined}
        onClick={() => (isOpen ? closeMenu() : openMenu())}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className="searchable-select-value">{selectedOption?.label ?? value}</span>
        <svg
          className="searchable-select-chevron"
          viewBox="0 0 16 16"
          width="16"
          height="16"
          fill="none"
          aria-hidden="true"
        >
          <path d="m4 6 4 4 4-4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {isOpen && createPortal(
        <div
          className="searchable-select-menu"
          ref={menuRef}
          style={menuStyle}
        >
          <input
            ref={searchRef}
            id={searchId}
            className="searchable-select-search"
            type="search"
            role="combobox"
            aria-label={`${searchPlaceholder} — ${label}`}
            aria-autocomplete="list"
            aria-expanded="true"
            aria-controls={listId}
            aria-activedescendant={activeIndex >= 0 && filteredOptions[activeIndex] ? `${generatedId}-option-${activeIndex}` : undefined}
            placeholder={searchPlaceholder}
            value={query}
            onChange={event => {
              setQuery(event.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={handleSearchKeyDown}
          />

          <ul className="searchable-select-options" id={listId} role="listbox" aria-label={label}>
            {filteredOptions.map((option, index) => {
              const isSelected = option.value === value;
              const isActive = index === activeIndex;

              return (
                <li
                  key={option.value}
                  ref={element => { optionRefs.current[index] = element; }}
                  id={`${generatedId}-option-${index}`}
                  className="searchable-select-option"
                  role="option"
                  aria-selected={isSelected}
                  data-active={isActive || undefined}
                  onMouseDown={event => event.preventDefault()}
                  onPointerMove={event => {
                    if (event.pointerType === "mouse") setActiveIndex(index);
                  }}
                  onClick={() => selectOption(option)}
                >
                  <span className="searchable-select-option-label">{option.label}</span>
                  {isSelected && (
                    <svg
                      className="searchable-select-check"
                      viewBox="0 0 16 16"
                      width="16"
                      height="16"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path d="m3 8 3.2 3.2L13 4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </li>
              );
            })}
          </ul>
          {!filteredOptions.length && (
            <div className="searchable-select-empty" role="status" aria-live="polite">
              {noResultsMessage}
            </div>
          )}
        </div>,
        document.body
      )}
    </div>
  );
}
