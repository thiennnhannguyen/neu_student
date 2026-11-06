import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';
import { useMemo, useState } from 'react';

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

/**
 * columns: [{ key, header, render?, sortValue?, sortable? }].
 * Header dính, hàng hover. Dưới 768px, CSS biến mỗi hàng thành thẻ và lấy nhãn từ data-label.
 */
export default function DataTable({ columns, rows, rowKey, ariaLabel, caption }) {
  const [sort, setSort] = useState(null);

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
    <div className="data-table-wrap table-scroll" role="region" aria-label={ariaLabel} tabIndex={0}>
      <table className="ui-table">
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
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((column) => (
                <td key={column.key} data-label={column.header}>
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
