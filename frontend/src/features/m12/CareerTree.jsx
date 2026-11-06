import { ChevronRight } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Badge, StatusChip } from '../../components/ui';
import { chipStatus, kindLabel, NO_CODE } from './labels';

/** Danh sách các nút đang thấy, theo đúng thứ tự trên màn hình, để di chuyển bằng phím. */
export function visibleItems(nodes, expanded) {
  return nodes.flatMap((node) => [
    { id: node.id, node },
    ...(expanded.has(node.id)
      ? node.children.map((child) => ({ id: `${node.id}/${child.id}`, node, child }))
      : []),
  ]);
}

function ChildRow({ child }) {
  return (
    <span className="career-tree__row">
      <span className="career-tree__title">
        {child.title}
        <span className="career-tree__meta">
          {child.kind === 'course' ? (child.code ?? NO_CODE) : kindLabel(child.kind)}
        </span>
      </span>
      <span className="career-tree__chips">
        <StatusChip status={chipStatus(child.kind, child.status)} size="sm" />
        {child.outside_curriculum && <Badge tone="outline">Ngoài CTĐT</Badge>}
      </span>
    </span>
  );
}

/**
 * Cây theo mẫu WAI-ARIA tree: một điểm dừng Tab; mũi tên lên, xuống đi giữa các nút; phải mở hoặc
 * vào nút con; trái đóng hoặc về nút cha; Home, End; Enter, Space để chọn. Mặc định thu gọn.
 */
export default function CareerTree({ label, nodes, onSelect }) {
  const [expanded, setExpanded] = useState(() => new Set());
  const [activeId, setActiveId] = useState(nodes[0]?.id ?? null);
  const moved = useRef(false);
  const refs = useRef(new Map());
  const items = visibleItems(nodes, expanded);

  useEffect(() => {
    if (moved.current) {
      refs.current.get(activeId)?.focus();
      moved.current = false;
    }
  }, [activeId, expanded]);

  function moveTo(id) {
    moved.current = true;
    setActiveId(id);
  }

  function setOpen(nodeId, open) {
    setExpanded((current) => {
      const next = new Set(current);
      if (open) {
        next.add(nodeId);
      } else {
        next.delete(nodeId);
      }
      return next;
    });
  }

  function activate(item) {
    if (item.child) {
      onSelect(item.child);
    } else {
      setOpen(item.node.id, !expanded.has(item.node.id));
    }
  }

  function handleRight(item) {
    if (item.child) {
      return;
    }
    if (!expanded.has(item.node.id)) {
      setOpen(item.node.id, true);
    } else if (item.node.children.length > 0) {
      moveTo(`${item.node.id}/${item.node.children[0].id}`);
    }
  }

  function handleLeft(item) {
    if (item.child) {
      moveTo(item.node.id);
    } else if (expanded.has(item.node.id)) {
      setOpen(item.node.id, false);
    }
  }

  function handleKeyDown(event) {
    const index = items.findIndex((entry) => entry.id === activeId);
    const item = items[index];
    const keys = {
      ArrowDown: () => items[index + 1] && moveTo(items[index + 1].id),
      ArrowUp: () => items[index - 1] && moveTo(items[index - 1].id),
      ArrowRight: () => handleRight(item),
      ArrowLeft: () => handleLeft(item),
      Home: () => moveTo(items[0].id),
      End: () => moveTo(items[items.length - 1].id),
      Enter: () => activate(item),
      ' ': () => activate(item),
    };
    if (keys[event.key]) {
      event.preventDefault();
      keys[event.key]();
    }
  }

  function bind(id) {
    return (element) => {
      if (element) {
        refs.current.set(id, element);
      } else {
        refs.current.delete(id);
      }
    };
  }

  return (
    // Bàn phím xử lý ở gốc cây vì mọi nút dùng chung một điểm dừng Tab.
    <ul role="tree" aria-label={label} className="career-tree" onKeyDown={handleKeyDown}>
      {nodes.map((node) => {
        const open = expanded.has(node.id);
        return (
          // eslint-disable-next-line jsx-a11y/click-events-have-key-events -- phím xử lý ở gốc cây
          <li
            key={node.id}
            ref={bind(node.id)}
            role="treeitem"
            aria-expanded={open}
            aria-level={1}
            aria-labelledby={`tree-group-${node.id}`}
            aria-selected={false}
            tabIndex={activeId === node.id ? 0 : -1}
            className="career-tree__group"
            onClick={(event) => {
              event.stopPropagation();
              setActiveId(node.id);
              setOpen(node.id, !open);
            }}
          >
            <span className="career-tree__row career-tree__row--group">
              <ChevronRight
                size={16}
                aria-hidden="true"
                className={`career-tree__chevron${open ? ' career-tree__chevron--open' : ''}`}
              />
              <span id={`tree-group-${node.id}`} className="career-tree__title">
                {node.title}
                <span className="career-tree__meta">
                  {node.short_desc ? `${node.short_desc} · ` : ''}
                  {node.children.length} yêu cầu
                </span>
              </span>
            </span>
            {open && (
              <ul role="group">
                {node.children.map((child) => {
                  const id = `${node.id}/${child.id}`;
                  return (
                    // eslint-disable-next-line jsx-a11y/click-events-have-key-events -- phím xử lý ở gốc cây
                    <li
                      key={child.id}
                      ref={bind(id)}
                      role="treeitem"
                      aria-level={2}
                      aria-selected={false}
                      tabIndex={activeId === id ? 0 : -1}
                      className="career-tree__item"
                      onClick={(event) => {
                        event.stopPropagation();
                        setActiveId(id);
                        onSelect(child);
                      }}
                    >
                      <ChildRow child={child} />
                    </li>
                  );
                })}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
