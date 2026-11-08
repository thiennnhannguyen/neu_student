import { ArrowDown, ArrowUp, ArrowUpDown, ChevronDown } from 'lucide-react';
import { Fragment, useId, useMemo, useState } from 'react';

function compareValues(first, second) {
  if (first === second) {
    return 0;
  }
  if (first === null || first === undefined) {
    return 1;
  }
  if (second === null || second === undefined) {
    return -1;
  }
  return String(first).localeCompare(String(second), 'vi', { numeric: true });
}

/** Hàng tổng: nhãn chiếm các cột trước ô đầu tiên có số, mỗi số nằm đúng dưới cột của nó. */
function TableFooter({ columns, footer, width }) {
  const first = columns.findIndex((column) => column.key in footer.cells);
  const span = Math.max(1, first);
  const rest = columns.slice(span);
  return (
    <tfoot>
      <tr className="ui-table__footer">
        <th scope="row" colSpan={span}>
          {footer.label}
        </th>
        {rest.map((column) => {
          const has = column.key in footer.cells;
          return (
            <td
              key={column.key}
              data-label={has ? column.header : undefined}
              className={has ? undefined : 'ui-table__blank'}
            >
              {has ? footer.cells[column.key] : null}
            </td>
          );
        })}
        {width > columns.length && <td className="ui-table__blank" />}
      </tr>
    </tfoot>
  );
}

/**
 * columns: [{ key, header, render?, sortValue?, sortable?, rowHeader?, isBlank? }].
 * Header dính, hàng hover. Dưới 768px, CSS biến mỗi hàng thành thẻ và lấy nhãn từ data-label.
 * rowHeader: ô là tiêu đề của hàng. isBlank(row): ô không có giá trị, được ẩn trên thẻ di động.
 * detail: { header, label(row), render(row) } thêm cột cuối có nút mở/đóng một hàng chi tiết ngay dưới.
 * footer: { label, cells: { [columnKey]: nội dung } } thêm hàng tổng ở tfoot, ô nằm đúng dưới cột.
 */
export default function DataTable({
  columns,
  rows,
  rowKey,
  ariaLabel,
  caption,
  className = '',
  detail,
  footer,
}) {
  const [sort, setSort] = useState(null);
  const [open, setOpen] = useState(() => new Set());
  const baseId = useId();
  const detailId = (key) =>
    `${baseId}-detail-${encodeURIComponent(String(key)).replace(/%/g, '_')}`;
  const width = columns.length + (detail ? 1 : 0);

  function toggleDetail(key) {
    setOpen((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  const sorted = useMemo(() => {
    if (!sort) {
      return rows;
    }
    const column = columns.find((item) => item.key === sort.key);
    const read = column.sortValue ?? ((row) => row[column.key]);
    const direction = sort.direction === 'asc' ? 1 : -1;
    return [...rows].sort((first, second) => direction * compareValues(read(first), read(second)));
  }, [columns, rows, sort]);

  function toggleSort(key) {
    setSort((current) =>
      current?.key === key && current.direction === 'asc'
        ? { key, direction: 'desc' }
        : { key, direction: 'asc' },
    );
  }

  function ariaSort(column) {
    if (!column.sortable) {
      return undefined;
    }
    if (sort?.key !== column.key) {
      return 'none';
    }
    return sort.direction === 'asc' ? 'ascending' : 'descending';
  }

  function sortIcon(column) {
    if (sort?.key !== column.key) {
      return ArrowUpDown;
    }
    return sort.direction === 'asc' ? ArrowUp : ArrowDown;
  }

  return (
    // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- cuộn được bằng bàn phím
    <div className="data-table-wrap" role="region" aria-label={ariaLabel} tabIndex={0}>
      <table className={`ui-table ${className}`.trim()}>
        {caption && <caption className="visually-hidden">{caption}</caption>}
        <thead>
          <tr>
            {columns.map((column) => {
              const SortIcon = sortIcon(column);
              return (
                <th key={column.key} scope="col" aria-sort={ariaSort(column)}>
                  {column.sortable ? (
                    <button
                      type="button"
                      className="ui-table__sort"
                      onClick={() => toggleSort(column.key)}
                    >
                      {column.header}
                      <SortIcon size={14} aria-hidden="true" />
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              );
            })}
            {detail && <th scope="col">{detail.header}</th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const key = rowKey(row);
            const expanded = open.has(key);
            return (
              <Fragment key={key}>
                <tr className={expanded ? 'ui-table__row--open' : undefined}>
                  {columns.map((column) => {
                    const content = column.render ? column.render(row) : row[column.key];
                    if (column.rowHeader) {
                      return (
                        <th key={column.key} scope="row" data-label={column.header}>
                          {content}
                        </th>
                      );
                    }
                    return (
                      <td
                        key={column.key}
                        data-label={column.header}
                        className={column.isBlank?.(row) ? 'ui-table__blank' : undefined}
                      >
                        {content}
                      </td>
                    );
                  })}
                  {detail && (
                    <td data-label={detail.header} className="ui-table__toggle-cell">
                      <button
                        type="button"
                        className="ui-table__toggle"
                        aria-expanded={expanded}
                        aria-controls={detailId(key)}
                        aria-label={detail.label(row)}
                        onClick={() => toggleDetail(key)}
                      >
                        <ChevronDown size={18} aria-hidden="true" />
                      </button>
                    </td>
                  )}
                </tr>
                {detail && expanded && (
                  <tr className="ui-table__detail">
                    <td id={detailId(key)} colSpan={width}>
                      {detail.render(row)}
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
        {footer && <TableFooter columns={columns} footer={footer} width={width} />}
      </table>
    </div>
  );
}
