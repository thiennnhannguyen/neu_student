import { useRef, useState } from 'react';

/** tabs: [{ id, label, content }]. Phím mũi tên, Home, End đổi tab theo mẫu ARIA. */
export default function Tabs({ tabs, label, idPrefix = 'tabs' }) {
  const [selected, setSelected] = useState(tabs[0].id);
  const buttons = useRef({});

  function move(event, index) {
    const last = tabs.length - 1;
    const target = {
      ArrowRight: index === last ? 0 : index + 1,
      ArrowLeft: index === 0 ? last : index - 1,
      Home: 0,
      End: last,
    }[event.key];
    if (target === undefined) {
      return;
    }
    event.preventDefault();
    setSelected(tabs[target].id);
    buttons.current[tabs[target].id]?.focus();
  }

  return (
    <div className="tabs">
      <div role="tablist" aria-label={label} className="tabs__list">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(node) => {
              buttons.current[tab.id] = node;
            }}
            type="button"
            role="tab"
            id={`${idPrefix}-tab-${tab.id}`}
            aria-selected={tab.id === selected}
            aria-controls={`${idPrefix}-panel-${tab.id}`}
            tabIndex={tab.id === selected ? 0 : -1}
            className="tabs__tab"
            onClick={() => setSelected(tab.id)}
            onKeyDown={(event) => move(event, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`${idPrefix}-panel-${tab.id}`}
          aria-labelledby={`${idPrefix}-tab-${tab.id}`}
          hidden={tab.id !== selected}
          className="tabs__panel"
        >
          {tab.id === selected && tab.content}
        </div>
      ))}
    </div>
  );
}
