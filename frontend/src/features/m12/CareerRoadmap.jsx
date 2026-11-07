import { ChevronRight } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Badge, StatusChip } from '../../components/ui';
import { chipStatus, NO_CODE, percentText, priorityLabel, typeLabel } from './labels';

export function courseChildren(node) {
  return node.children.filter((child) => child.kind === 'course');
}

/** Danh sách các nút đang thấy, theo đúng thứ tự trên màn hình, để di chuyển bằng phím. */
export function visibleItems(nodes, expanded) {
  return nodes.flatMap((node) => [
    { id: node.id, node },
    ...(expanded.has(node.id)
      ? courseChildren(node).map((child) => ({ id: `${node.id}/${child.id}`, node, child }))
      : []),
  ]);
}

function CourseRow({ child }) {
  const type = typeLabel(child.requirement_type);
  const priority = priorityLabel(child.priority);
  return (
    <span className="roadmap__course">
      <span className="roadmap__course-title">
        {child.title}
        <span className="roadmap__course-meta">
          {!child.not_in_program && <span>{child.code ?? NO_CODE}</span>}
          {type && <span>{type}</span>}
          {child.planned_semester && <span>HK {child.planned_semester}</span>}
          {priority && <span>{priority}</span>}
        </span>
      </span>
      <span className="roadmap__course-chips">
        <StatusChip status={chipStatus(child.kind, child.status)} />
        {child.outside_curriculum && <Badge tone="outline">Ngoài CTĐT</Badge>}
      </span>
    </span>
  );
}

/**
 * Lộ trình dạng timeline dọc, theo mẫu WAI-ARIA tree: một điểm dừng Tab; mũi tên lên, xuống đi giữa
 * các nút; phải mở hoặc vào nút con; trái đóng hoặc về giai đoạn; Home, End; Enter, Space để chọn.
 * Mặc định mở hết để trạng thái từng môn luôn thấy.
 */
export default function CareerRoadmap({ label, nodes, onSelect }) {
  const [expanded, setExpanded] = useState(() => new Set(nodes.map((node) => node.id)));
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
    const courses = courseChildren(item.node);
    if (!expanded.has(item.node.id)) {
      setOpen(item.node.id, true);
    } else if (courses.length > 0) {
      moveTo(`${item.node.id}/${courses[0].id}`);
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
    <ul role="tree" aria-label={label} className="roadmap" onKeyDown={handleKeyDown}>
      {nodes.map((node) => {
        const open = expanded.has(node.id);
        const courses = courseChildren(node);
        return (
          <li key={node.id} role="none" className="roadmap__stage">
            <span className="roadmap__marker" aria-hidden="true">
              {node.order}
            </span>
            {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events -- phím xử lý ở gốc cây */}
            <div
              ref={bind(node.id)}
              role="treeitem"
              aria-expanded={open}
              aria-level={1}
              aria-selected={false}
              tabIndex={activeId === node.id ? 0 : -1}
              className="roadmap__stage-row"
              onClick={() => {
                setActiveId(node.id);
                setOpen(node.id, !open);
              }}
            >
              <span className="roadmap__head">
                <ChevronRight
                  size={16}
                  aria-hidden="true"
                  className={`roadmap__chevron${open ? ' roadmap__chevron--open' : ''}`}
                />
                <span className="roadmap__title">{node.title}</span>{' '}
                <strong className="roadmap__percent">
                  {percentText(node.course_progress?.percent)}
                </strong>
              </span>{' '}
              {node.deliverable && (
                <span className="roadmap__deliverable">
                  <strong>Sản phẩm cần đạt: </strong>
                  {node.deliverable}
                </span>
              )}
            </div>
            {open &&
              (courses.length > 0 ? (
                <ul role="group" className="roadmap__courses">
                  {courses.map((child) => {
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
                        className={`roadmap__item${child.not_in_program ? ' roadmap__item--absent' : ''}`}
                        onClick={(event) => {
                          event.stopPropagation();
                          setActiveId(id);
                          onSelect(child);
                        }}
                      >
                        <CourseRow child={child} />
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <span className="roadmap__empty">Giai đoạn này là dự án, không có học phần.</span>
              ))}
          </li>
        );
      })}
    </ul>
  );
}
